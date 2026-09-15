#include "mfem.hpp"
#include <osqp.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

using namespace mfem;

namespace
{
constexpr double x_min = -30.0, x_max = 30.0;
constexpr double y_min = -40.0, y_max = 40.0;
constexpr double z_min = -10.0, z_max = 70.0;
constexpr double dt = 0.00015625;
constexpr int subcells = 3;
constexpr int test_count = 4;

class LorenzDrift final : public VectorCoefficient
{
public:
   LorenzDrift() : VectorCoefficient(3) { }

   void Eval(Vector &value, ElementTransformation &transformation,
             const IntegrationPoint &point) override
   {
      Vector x(3);
      transformation.Transform(point, x);
      value.SetSize(3);
      value[0] = 10.0 * (x[1] - x[0]);
      value[1] = x[0] * (28.0 - x[2]) - x[1];
      value[2] = x[0] * x[1] - (8.0 / 3.0) * x[2];
   }
};

class DolfinxPenaltyDGDiffusionIntegrator final : public DGDiffusionIntegrator
{
public:
   DolfinxPenaltyDGDiffusionIntegrator(MatrixCoefficient &coefficient,
                                       const double sigma,
                                       const double penalty_times_degree_squared)
      : DGDiffusionIntegrator(coefficient, sigma, 1.0),
        penalty_factor(penalty_times_degree_squared) { }

   void AssembleFaceMatrix(const FiniteElement &element1,
                           const FiniteElement &element2,
                           FaceElementTransformations &transformation,
                           DenseMatrix &matrix) override
   {
      IntegrationPoint center;
      center.Set2(0.5, 0.5);
      transformation.SetAllIntPoints(&center);
      Vector face_normal(3);
      CalcOrtho(transformation.Jacobian(), face_normal);
      const double face_scale = face_normal.Norml2();
      auto geometry = [face_scale](ElementTransformation &element)
      {
         const DenseMatrix &jacobian = element.Jacobian();
         double diameter_squared = 0.0;
         for (int i = 0; i < jacobian.Height(); ++i)
         {
            for (int j = 0; j < jacobian.Width(); ++j)
            {
               diameter_squared += jacobian(i, j) * jacobian(i, j);
            }
         }
         return std::pair<double, double>(
            element.Weight() / face_scale, std::sqrt(diameter_squared));
      };
      const auto first = geometry(*transformation.Elem1);
      const auto second = geometry(*transformation.Elem2);
      kappa = 4.0 * penalty_factor
              / ((first.second + second.second)
                 * (1.0 / first.first + 1.0 / second.first));
      DGDiffusionIntegrator::AssembleFaceMatrix(
         element1, element2, transformation, matrix);
   }

private:
   double penalty_factor;
};

double TestValue(const int test, const int ix, const int iy, const int iz,
                 const double r, const double s, const double t)
{
   if (test == 0)
   {
      return 1.0 + 0.07 * r - 0.04 * s + 0.03 * t
             + 0.02 * r * s - 0.015 * s * t + 0.01 * r * r;
   }
   if (test == 1)
   {
      const double parity = ((ix + iy + iz) % 2 == 0) ? 1.0 : -1.0;
      return (1.0 + 0.08 * parity)
             * (1.0 + 0.11 * r + 0.04 * s * s - 0.06 * t
                + 0.025 * r * t);
   }
   if (test == 2)
   {
      const double cell_mode = 0.04 * std::sin(0.7 * (ix + 1))
                            - 0.03 * std::cos(0.5 * (iy + 2))
                            + 0.02 * ((iz % 3) - 1);
      return 0.9 + cell_mode + 0.06 * r * r - 0.05 * s
             + 0.035 * t * t + 0.02 * r * s * t;
   }
   // Positive average with genuine within-cell negativity.  This makes the
   // corrected-step gate exercise the QP rather than only its no-op path.
   return 1.0 + 2.4 * (r - 0.5) + 0.8 * (s - 0.5)
          - 0.5 * (t - 0.5);
}

void CellIndexAndOrigin(ElementTransformation &transformation,
                        const int nx, const int ny, const int nz,
                        int &ix, int &iy, int &iz)
{
   IntegrationPoint center;
   center.Set3(0.5, 0.5, 0.5);
   Vector x(3);
   transformation.Transform(center, x);
   const double hx = (x_max - x_min) / nx;
   const double hy = (y_max - y_min) / ny;
   const double hz = (z_max - z_min) / nz;
   ix = std::clamp(static_cast<int>(std::floor((x[0] - x_min) / hx)), 0, nx - 1);
   iy = std::clamp(static_cast<int>(std::floor((x[1] - y_min) / hy)), 0, ny - 1);
   iz = std::clamp(static_cast<int>(std::floor((x[2] - z_min) / hz)), 0, nz - 1);
}

void PopulateState(ParFiniteElementSpace &space, ParGridFunction &field,
                   const int test, const int nx, const int ny, const int nz)
{
   field = 0.0;
   Array<int> dofs;
   for (int element = 0; element < space.GetNE(); ++element)
   {
      const FiniteElement *fe = space.GetFE(element);
      const IntegrationRule &nodes = fe->GetNodes();
      ElementTransformation *transformation = space.GetElementTransformation(element);
      int ix, iy, iz;
      CellIndexAndOrigin(*transformation, nx, ny, nz, ix, iy, iz);
      Vector values(nodes.GetNPoints());
      for (int local = 0; local < nodes.GetNPoints(); ++local)
      {
         const IntegrationPoint &point = nodes.IntPoint(local);
         values[local] = TestValue(test, ix, iy, iz, point.x, point.y, point.z);
      }
      space.GetElementVDofs(element, dofs);
      field.SetSubVector(dofs, values);
   }
}

void ConfigureMassSolver(HypreParMatrix &matrix, HyprePCG &solver,
                         HypreDiagScale &preconditioner)
{
   preconditioner.SetOperator(matrix);
   solver.SetOperator(matrix);
   solver.SetPreconditioner(preconditioner);
   solver.SetTol(1.0e-14);
   solver.SetAbsTol(1.0e-16);
   solver.SetMaxIter(500);
   solver.SetPrintLevel(0);
   solver.iterative_mode = false;
}

void ExportSubcellAverages(const ParGridFunction &field,
                           const int nx, const int ny, const int nz,
                           const std::filesystem::path &path)
{
   const int rank = Mpi::WorldRank();
   const int gx_count = nx * subcells;
   const int gy_count = ny * subcells;
   const int gz_count = nz * subcells;
   const std::size_t value_count = static_cast<std::size_t>(gx_count)
                                   * gy_count * gz_count;
   std::vector<double> local(value_count, 0.0);
   std::vector<double> global(rank == 0 ? value_count : 0, 0.0);
   const double q[3] = {
      0.5 * (1.0 - std::sqrt(3.0 / 5.0)), 0.5,
      0.5 * (1.0 + std::sqrt(3.0 / 5.0))
   };
   const double w[3] = {5.0 / 18.0, 8.0 / 18.0, 5.0 / 18.0};

   ParFiniteElementSpace *space = field.ParFESpace();
   for (int element = 0; element < space->GetNE(); ++element)
   {
      ElementTransformation *transformation = space->GetElementTransformation(element);
      int ix, iy, iz;
      CellIndexAndOrigin(*transformation, nx, ny, nz, ix, iy, iz);
      for (int sx = 0; sx < subcells; ++sx)
      {
         for (int sy = 0; sy < subcells; ++sy)
         {
            for (int sz = 0; sz < subcells; ++sz)
            {
               double average = 0.0;
               for (int i = 0; i < 3; ++i)
               {
                  for (int j = 0; j < 3; ++j)
                  {
                     for (int k = 0; k < 3; ++k)
                     {
                        IntegrationPoint point;
                        point.Set3((sx + q[i]) / subcells,
                                   (sy + q[j]) / subcells,
                                   (sz + q[k]) / subcells);
                        average += w[i] * w[j] * w[k]
                                   * field.GetValue(element, point);
                     }
                  }
               }
               const int gx = ix * subcells + sx;
               const int gy = iy * subcells + sy;
               const int gz = iz * subcells + sz;
               const std::size_t index = (static_cast<std::size_t>(gx) * gy_count + gy)
                                         * gz_count + gz;
               local[index] = average;
            }
         }
      }
   }
   MPI_Reduce(local.data(), rank == 0 ? global.data() : nullptr,
              static_cast<int>(value_count), MPI_DOUBLE, MPI_SUM, 0,
              MPI_COMM_WORLD);
   if (rank == 0)
   {
      std::ofstream output(path, std::ios::binary);
      MFEM_VERIFY(output.good(), "could not open physical-field export");
      output.write(reinterpret_cast<const char *>(global.data()),
                   static_cast<std::streamsize>(global.size() * sizeof(double)));
   }
}

class LocalQ2Projector
{
public:
   LocalQ2Projector()
   {
      constexpr int variables = 27;
      constexpr int bernstein_rows = 216;
      constexpr int rows = bernstein_rows + 1;
      const double one_dimensional_mass[3][3] = {
         {4.0 / 30.0, 2.0 / 30.0, -1.0 / 30.0},
         {2.0 / 30.0, 16.0 / 30.0, 2.0 / 30.0},
         {-1.0 / 30.0, 2.0 / 30.0, 4.0 / 30.0}
      };
      const double one_dimensional_average[3] = {1.0 / 6.0, 2.0 / 3.0, 1.0 / 6.0};
      // Nodal Q2 values at 0, 1/2, 1 to Bernstein coefficients on
      // [0,1/2] and [1/2,1], in subcell/control-point order.
      const double transform[6][3] = {
         {1.0, 0.0, 0.0},
         {0.25, 1.0, -0.25},
         {0.0, 1.0, 0.0},
         {0.0, 1.0, 0.0},
         {-0.25, 1.0, 0.25},
         {0.0, 0.0, 1.0}
      };
      hessian.assign(variables * variables, 0.0);
      average.assign(variables, 0.0);
      constraints.assign(bernstein_rows * variables, 0.0);
      auto index = [](const int i, const int j, const int k)
      { return (i * 3 + j) * 3 + k; };
      for (int i = 0; i < 3; ++i)
      for (int j = 0; j < 3; ++j)
      for (int k = 0; k < 3; ++k)
      {
         const int row = index(i, j, k);
         average[row] = one_dimensional_average[i]
                        * one_dimensional_average[j]
                        * one_dimensional_average[k];
         for (int a = 0; a < 3; ++a)
         for (int b = 0; b < 3; ++b)
         for (int c = 0; c < 3; ++c)
         {
            const int column = index(a, b, c);
            hessian[row * variables + column] = one_dimensional_mass[i][a]
               * one_dimensional_mass[j][b] * one_dimensional_mass[k][c];
         }
      }
      int constraint_row = 0;
      for (int a = 0; a < 6; ++a)
      for (int b = 0; b < 6; ++b)
      for (int c = 0; c < 6; ++c, ++constraint_row)
      {
         for (int i = 0; i < 3; ++i)
         for (int j = 0; j < 3; ++j)
         for (int k = 0; k < 3; ++k)
         {
            constraints[constraint_row * variables + index(i, j, k)] =
               transform[a][i] * transform[b][j] * transform[c][k];
         }
      }

      // OSQP stores the upper Hessian triangle and the constraint matrix in CSC.
      p_columns.resize(variables + 1);
      for (int column = 0; column < variables; ++column)
      {
         p_columns[column] = static_cast<OSQPInt>(p_values.size());
         for (int row = 0; row <= column; ++row)
         {
            p_rows.push_back(row);
            p_values.push_back(hessian[row * variables + column]);
         }
      }
      p_columns[variables] = static_cast<OSQPInt>(p_values.size());
      a_columns.resize(variables + 1);
      for (int column = 0; column < variables; ++column)
      {
         a_columns[column] = static_cast<OSQPInt>(a_values.size());
         for (int row = 0; row < bernstein_rows; ++row)
         {
            a_rows.push_back(row);
            a_values.push_back(constraints[row * variables + column]);
         }
         a_rows.push_back(bernstein_rows);
         a_values.push_back(average[column]);
      }
      a_columns[variables] = static_cast<OSQPInt>(a_values.size());
      q.assign(variables, 0.0);
      lower.assign(rows, positivity_margin);
      upper.assign(rows, OSQP_INFTY);
      lower.back() = 1.0;
      upper.back() = 1.0;
      P = OSQPCscMatrix_new(variables, variables, p_values.size(),
                            p_values.data(), p_rows.data(), p_columns.data());
      A = OSQPCscMatrix_new(rows, variables, a_values.size(),
                            a_values.data(), a_rows.data(), a_columns.data());
      settings = OSQPSettings_new();
      settings->verbose = 0;
      settings->warm_starting = 1;
      settings->polishing = 1;
      settings->eps_abs = 1.0e-11;
      settings->eps_rel = 1.0e-11;
      settings->max_iter = 10000;
      const OSQPInt error = osqp_setup(
         &solver, P, q.data(), A, lower.data(), upper.data(), rows, variables, settings);
      MFEM_VERIFY(error == 0 && solver != nullptr, "OSQP local-Q2 setup failed");
   }

   ~LocalQ2Projector()
   {
      if (solver) { osqp_cleanup(solver); }
      if (settings) { OSQPSettings_free(settings); }
      if (A) { OSQPCscMatrix_free(A); }
      if (P) { OSQPCscMatrix_free(P); }
   }

   bool Project(const std::array<double, 27> &raw,
                std::array<double, 27> &result)
   {
      constexpr int variables = 27;
      constexpr int bernstein_rows = 216;
      double cell_average = 0.0;
      for (int i = 0; i < variables; ++i) { cell_average += average[i] * raw[i]; }
      MFEM_VERIFY(cell_average >= -1.0e-12,
                  "corrected-step diagnostic encountered a negative cell average");
      if (cell_average <= 0.0)
      {
         result.fill(0.0);
         return true;
      }
      std::array<double, variables> normalized{};
      double minimum = OSQP_INFTY;
      for (int i = 0; i < variables; ++i) { normalized[i] = raw[i] / cell_average; }
      for (int row = 0; row < bernstein_rows; ++row)
      {
         double value = 0.0;
         for (int column = 0; column < variables; ++column)
         {
            value += constraints[row * variables + column] * normalized[column];
         }
         minimum = std::min(minimum, value);
      }
      if (minimum >= positivity_margin)
      {
         result = raw;
         return false;
      }
      for (int row = 0; row < variables; ++row)
      {
         q[row] = 0.0;
         for (int column = 0; column < variables; ++column)
         {
            q[row] -= hessian[row * variables + column] * normalized[column];
         }
      }
      MFEM_VERIFY(osqp_update_data_vec(solver, q.data(), nullptr, nullptr) == 0,
                  "OSQP local-Q2 vector update failed");
      MFEM_VERIFY(osqp_solve(solver) == 0, "OSQP local-Q2 solve failed");
      MFEM_VERIFY(solver->info->status_val == OSQP_SOLVED
                  || solver->info->status_val == OSQP_SOLVED_INACCURATE,
                  "OSQP local-Q2 optimization did not converge");
      std::array<double, variables> candidate{};
      double candidate_average = 0.0;
      for (int i = 0; i < variables; ++i)
      {
         candidate[i] = solver->solution->x[i];
         candidate_average += average[i] * candidate[i];
      }
      for (double &value : candidate) { value += 1.0 - candidate_average; }
      minimum = OSQP_INFTY;
      for (int row = 0; row < bernstein_rows; ++row)
      {
         double value = 0.0;
         for (int column = 0; column < variables; ++column)
         {
            value += constraints[row * variables + column] * candidate[column];
         }
         minimum = std::min(minimum, value);
      }
      if (minimum < positivity_margin)
      {
         const double theta = std::clamp(
            (1.0 - positivity_margin) / (1.0 - minimum), 0.0, 1.0);
         for (double &value : candidate) { value = 1.0 + theta * (value - 1.0); }
      }
      for (int i = 0; i < variables; ++i) { result[i] = cell_average * candidate[i]; }
      return true;
   }

private:
   static constexpr double positivity_margin = 1.0e-12;
   std::vector<double> hessian, average, constraints;
   std::vector<OSQPFloat> p_values, a_values, q, lower, upper;
   std::vector<OSQPInt> p_rows, p_columns, a_rows, a_columns;
   OSQPCscMatrix *P = nullptr;
   OSQPCscMatrix *A = nullptr;
   OSQPSettings *settings = nullptr;
   OSQPSolver *solver = nullptr;
};

int ProjectField(LocalQ2Projector &projector, ParFiniteElementSpace &space,
                 const ParGridFunction &raw, ParGridFunction &corrected)
{
   corrected = 0.0;
   int local_projected = 0;
   Array<int> dofs;
   for (int element = 0; element < space.GetNE(); ++element)
   {
      std::array<double, 27> nodal{}, projected{};
      for (int i = 0; i < 3; ++i)
      for (int j = 0; j < 3; ++j)
      for (int k = 0; k < 3; ++k)
      {
         IntegrationPoint point;
         point.Set3(0.5 * i, 0.5 * j, 0.5 * k);
         nodal[(i * 3 + j) * 3 + k] = raw.GetValue(element, point);
      }
      local_projected += projector.Project(nodal, projected) ? 1 : 0;
      const IntegrationRule &nodes = space.GetFE(element)->GetNodes();
      Vector values(nodes.GetNPoints());
      for (int local = 0; local < nodes.GetNPoints(); ++local)
      {
         const IntegrationPoint &point = nodes.IntPoint(local);
         const int i = std::clamp(static_cast<int>(std::lround(2.0 * point.x)), 0, 2);
         const int j = std::clamp(static_cast<int>(std::lround(2.0 * point.y)), 0, 2);
         const int k = std::clamp(static_cast<int>(std::lround(2.0 * point.z)), 0, 2);
         values[local] = projected[(i * 3 + j) * 3 + k];
      }
      space.GetElementVDofs(element, dofs);
      corrected.SetSubVector(dofs, values);
   }
   int global_projected = 0;
   MPI_Allreduce(&local_projected, &global_projected, 1, MPI_INT, MPI_SUM,
                 MPI_COMM_WORLD);
   return global_projected;
}
}

int main(int argc, char *argv[])
{
   Mpi::Init(argc, argv);
   const int rank = Mpi::WorldRank();
   MFEM_VERIFY(argc == 5,
               "usage: mfem_physical_equivalence NX NY NZ OUTPUT_DIRECTORY");
   const int nx = std::stoi(argv[1]);
   const int ny = std::stoi(argv[2]);
   const int nz = std::stoi(argv[3]);
   // FFCx selects these effective Gauss orders for the frozen combined form
   // and for the isolated diagnostic form, respectively.  The upwind switch
   // makes the face integrand piecewise polynomial, so matching the actual
   // incumbent quadrature is part of operator equivalence.
   constexpr int combined_face_quadrature_order = 14;
   constexpr int isolated_advection_face_quadrature_order = 12;
   const std::filesystem::path output_directory(argv[4]);
   MFEM_VERIFY(nx > 0 && ny > 0 && nz > 0, "positive mesh sizes required");
   if (rank == 0) { std::filesystem::create_directories(output_directory); }
   MPI_Barrier(MPI_COMM_WORLD);

   Mesh serial = Mesh::MakeCartesian3D(
      nx, ny, nz, Element::HEXAHEDRON,
      x_max - x_min, y_max - y_min, z_max - z_min);
   for (int vertex = 0; vertex < serial.GetNV(); ++vertex)
   {
      double *x = serial.GetVertex(vertex);
      x[0] += x_min;
      x[1] += y_min;
      x[2] += z_min;
   }
   ParMesh mesh(MPI_COMM_WORLD, serial);
   L2_FECollection collection(2, 3, BasisType::GaussLobatto);
   ParFiniteElementSpace space(&mesh, &collection);

   ConstantCoefficient one(1.0);
   DenseMatrix tensor(3);
   tensor = 0.0;
   tensor(0, 0) = 1.0; tensor(0, 1) = 0.4; tensor(0, 2) = 0.2;
   tensor(1, 0) = 0.4; tensor(1, 1) = 1.0; tensor(1, 2) = 0.3;
   tensor(2, 0) = 0.2; tensor(2, 1) = 0.3; tensor(2, 2) = 1.0;
   DenseMatrix negative_tensor(tensor);
   negative_tensor *= -1.0;
   MatrixConstantCoefficient negative_diffusion(negative_tensor);
   LorenzDrift drift;

   ParBilinearForm mass(&space);
   mass.AddDomainIntegrator(new MassIntegrator(one));
   mass.Assemble();
   mass.Finalize();
   HypreParMatrix *M = mass.ParallelAssemble();

   constexpr double sigma = -1.0;
   constexpr double penalty_times_degree_squared = 64.0;
   ParBilinearForm spatial(&space);
   auto *volume_advection = new ConservativeConvectionIntegrator(drift, -1.0);
   volume_advection->SetIntRule(&IntRules.Get(Geometry::CUBE, 6));
   spatial.AddDomainIntegrator(volume_advection);
   auto *face_advection = new DGTraceIntegrator(drift, -1.0, -0.5);
   face_advection->SetIntRule(
      &IntRules.Get(Geometry::SQUARE, combined_face_quadrature_order));
   spatial.AddInteriorFaceIntegrator(face_advection);
   spatial.AddDomainIntegrator(new DiffusionIntegrator(negative_diffusion));
   spatial.AddInteriorFaceIntegrator(new DolfinxPenaltyDGDiffusionIntegrator(
      negative_diffusion, sigma, penalty_times_degree_squared));
   spatial.Assemble();
   spatial.Finalize();
   HypreParMatrix *A = spatial.ParallelAssemble();

   const bool extended_diagnostics = nx * ny * nz <= 1000;
   HypreParMatrix *A_advection = nullptr;
   HypreParMatrix *A_advection_volume = nullptr;
   HypreParMatrix *A_advection_face = nullptr;
   HypreParMatrix *A_diffusion = nullptr;
   if (extended_diagnostics)
   {
      ParBilinearForm advection(&space);
      auto *volume_advection_only = new ConservativeConvectionIntegrator(drift, -1.0);
      volume_advection_only->SetIntRule(&IntRules.Get(Geometry::CUBE, 6));
      advection.AddDomainIntegrator(volume_advection_only);
      auto *face_advection_only = new DGTraceIntegrator(drift, -1.0, -0.5);
      face_advection_only->SetIntRule(
         &IntRules.Get(Geometry::SQUARE, isolated_advection_face_quadrature_order));
      advection.AddInteriorFaceIntegrator(face_advection_only);
      advection.Assemble();
      advection.Finalize();
      A_advection = advection.ParallelAssemble();

      ParBilinearForm advection_volume(&space);
      auto *volume_advection_diagnostic = new ConservativeConvectionIntegrator(drift, -1.0);
      volume_advection_diagnostic->SetIntRule(&IntRules.Get(Geometry::CUBE, 6));
      advection_volume.AddDomainIntegrator(volume_advection_diagnostic);
      advection_volume.Assemble();
      advection_volume.Finalize();
      A_advection_volume = advection_volume.ParallelAssemble();

      ParBilinearForm advection_face(&space);
      auto *face_advection_diagnostic = new DGTraceIntegrator(drift, -1.0, -0.5);
      face_advection_diagnostic->SetIntRule(
         &IntRules.Get(Geometry::SQUARE, isolated_advection_face_quadrature_order));
      advection_face.AddInteriorFaceIntegrator(face_advection_diagnostic);
      advection_face.Assemble();
      advection_face.Finalize();
      A_advection_face = advection_face.ParallelAssemble();

      ParBilinearForm diffusion_form(&space);
      diffusion_form.AddDomainIntegrator(new DiffusionIntegrator(negative_diffusion));
      diffusion_form.AddInteriorFaceIntegrator(new DolfinxPenaltyDGDiffusionIntegrator(
         negative_diffusion, sigma, penalty_times_degree_squared));
      diffusion_form.Assemble();
      diffusion_form.Finalize();
      A_diffusion = diffusion_form.ParallelAssemble();
   }

   HypreParMatrix *cn_left = Add(1.0, *M, -0.5 * dt, *A);
   HypreParMatrix *cn_right = Add(1.0, *M, 0.5 * dt, *A);
   HypreDiagScale mass_preconditioner(*M);
   HyprePCG mass_solver(*M);
   ConfigureMassSolver(*M, mass_solver, mass_preconditioner);
   LocalQ2Projector local_projector;

   std::vector<double> derivative_residuals;
   std::vector<double> cn_residuals;
   std::vector<int> qp_projected_cells;
   for (int test = 0; test < test_count; ++test)
   {
      ParGridFunction initial(&space);
      PopulateState(space, initial, test, nx, ny, nz);
      Vector initial_true;
      initial.GetTrueDofs(initial_true);

      Vector action(A->Height());
      A->Mult(initial_true, action);
      Vector derivative(action.Size());
      mass_solver.Mult(action, derivative);
      ParGridFunction derivative_field(&space);
      derivative_field.SetFromTrueDofs(derivative);

      Vector derivative_check(action);
      M->AddMult(derivative, derivative_check, -1.0);
      const double local_derivative[2] = {
         derivative_check * derivative_check, action * action
      };
      double global_derivative[2] = {0.0, 0.0};
      MPI_Allreduce(local_derivative, global_derivative, 2, MPI_DOUBLE, MPI_SUM,
                    MPI_COMM_WORLD);
      derivative_residuals.push_back(
         std::sqrt(global_derivative[0] / global_derivative[1]));

      Vector rhs(cn_right->Height());
      cn_right->Mult(initial_true, rhs);
      Vector next(initial_true);
      HypreILU cn_preconditioner;
      cn_preconditioner.SetType(0);
      cn_preconditioner.SetLevelOfFill(1);
      cn_preconditioner.SetMaxIter(1);
      cn_preconditioner.SetTol(0.0);
      cn_preconditioner.SetPrintLevel(0);
      cn_preconditioner.SetOperator(*cn_left);
      HypreGMRES cn_solver(*cn_left);
      cn_solver.SetTol(1.0e-14);
      cn_solver.SetAbsTol(1.0e-17);
      cn_solver.SetMaxIter(1000);
      cn_solver.SetKDim(100);
      cn_solver.SetPrintLevel(0);
      cn_solver.SetPreconditioner(cn_preconditioner);
      cn_solver.iterative_mode = false;
      cn_solver.Mult(rhs, next);
      ParGridFunction next_field(&space);
      next_field.SetFromTrueDofs(next);
      ParGridFunction corrected_field(&space);
      qp_projected_cells.push_back(
         ProjectField(local_projector, space, next_field, corrected_field));

      Vector cn_check(rhs);
      cn_left->AddMult(next, cn_check, -1.0);
      const double local_cn[2] = {cn_check * cn_check, rhs * rhs};
      double global_cn[2] = {0.0, 0.0};
      MPI_Allreduce(local_cn, global_cn, 2, MPI_DOUBLE, MPI_SUM,
                    MPI_COMM_WORLD);
      cn_residuals.push_back(std::sqrt(global_cn[0] / global_cn[1]));

      ExportSubcellAverages(initial, nx, ny, nz,
                            output_directory / ("state_" + std::to_string(test) + ".bin"));
      ExportSubcellAverages(derivative_field, nx, ny, nz,
                            output_directory / ("action_" + std::to_string(test) + ".bin"));
      if (extended_diagnostics)
      {
         auto export_component = [&](HypreParMatrix &component, const std::string &name)
         {
            Vector component_action(component.Height());
            component.Mult(initial_true, component_action);
            Vector component_derivative(component_action.Size());
            mass_solver.Mult(component_action, component_derivative);
            ParGridFunction component_field(&space);
            component_field.SetFromTrueDofs(component_derivative);
            ExportSubcellAverages(component_field, nx, ny, nz,
                                  output_directory / (name + "_" + std::to_string(test) + ".bin"));
         };
         export_component(*A_advection, "advection");
         export_component(*A_advection_volume, "advection_volume");
         export_component(*A_advection_face, "advection_face");
         export_component(*A_diffusion, "diffusion");
      }
      ExportSubcellAverages(next_field, nx, ny, nz,
                            output_directory / ("cn_" + std::to_string(test) + ".bin"));
      ExportSubcellAverages(corrected_field, nx, ny, nz,
                            output_directory / ("qp_" + std::to_string(test) + ".bin"));
   }

   if (rank == 0)
   {
      std::ofstream summary(output_directory / "mfem_summary.json");
      summary << std::setprecision(17)
              << "{\n  \"mesh\": [" << nx << ", " << ny << ", " << nz << "],\n"
              << "  \"subcells_per_cell\": " << subcells << ",\n"
              << "  \"test_count\": " << test_count << ",\n"
              << "  \"extended_component_diagnostics\": "
              << (extended_diagnostics ? "true" : "false") << ",\n"
              << "  \"combined_face_quadrature_order\": "
              << combined_face_quadrature_order << ",\n"
              << "  \"isolated_advection_face_quadrature_order\": "
              << isolated_advection_face_quadrature_order << ",\n"
              << "  \"global_q2_dofs\": " << space.GlobalTrueVSize() << ",\n"
              << "  \"mass_inverse_relative_residuals\": [";
      for (int i = 0; i < test_count; ++i)
      {
         if (i) { summary << ", "; }
         summary << derivative_residuals[i];
      }
      summary << "],\n  \"cn_true_relative_residuals\": [";
      for (int i = 0; i < test_count; ++i)
      {
         if (i) { summary << ", "; }
         summary << cn_residuals[i];
      }
      summary << "],\n  \"qp_projected_cells\": [";
      for (int i = 0; i < test_count; ++i)
      {
         if (i) { summary << ", "; }
         summary << qp_projected_cells[i];
      }
      summary << "]\n}\n";
      std::cout << "MFEM physical exports written to " << output_directory << "\n";
   }

   delete cn_right;
   delete cn_left;
   if (A_diffusion) { delete A_diffusion; }
   if (A_advection_face) { delete A_advection_face; }
   if (A_advection_volume) { delete A_advection_volume; }
   if (A_advection) { delete A_advection; }
   delete A;
   delete M;
   return 0;
}
