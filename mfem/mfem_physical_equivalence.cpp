#include "mfem.hpp"
#include <osqp.h>

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <string>
#include <sys/resource.h>
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

class MatureGaussianMixture final : public Coefficient
{
public:
   explicit MatureGaussianMixture(const std::filesystem::path &path)
   {
      std::ifstream input(path, std::ios::binary | std::ios::ate);
      MFEM_VERIFY(input.good(), "could not open frozen mature mixture parameters");
      const auto bytes = input.tellg();
      MFEM_VERIFY(bytes > 0 && bytes % static_cast<std::streamoff>(13 * sizeof(double)) == 0,
                  "mature mixture parameter size is invalid");
      parameters.resize(static_cast<std::size_t>(bytes) / sizeof(double));
      input.seekg(0);
      input.read(reinterpret_cast<char *>(parameters.data()), bytes);
      MFEM_VERIFY(input.good(), "could not read mature mixture parameters");
   }

   double Eval(ElementTransformation &transformation,
               const IntegrationPoint &point) override
   {
      Vector x(3);
      transformation.Transform(point, x);
      double density = 0.0;
      for (std::size_t component = 0; component < parameters.size(); component += 13)
      {
         const double dx[3] = {x[0] - parameters[component + 1],
                               x[1] - parameters[component + 2],
                               x[2] - parameters[component + 3]};
         double exponent = 0.0;
         for (int row = 0; row < 3; ++row)
         for (int column = 0; column < 3; ++column)
         {
            exponent += dx[row] * parameters[component + 4 + 3 * row + column]
                        * dx[column];
         }
         density += parameters[component] * std::exp(-0.5 * exponent);
      }
      return density;
   }

private:
   std::vector<double> parameters;
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
      MFEM_VERIFY(face_scale > 0.0, "degenerate DG face");
      auto geometry = [&face_normal, face_scale](ElementTransformation &element)
      {
         const DenseMatrix &jacobian = element.Jacobian();
         double diameter_squared = 0.0;
         double normal_width = 0.0;
         for (int column = 0; column < jacobian.Width(); ++column)
         {
            double normal_projection = 0.0;
            for (int row = 0; row < jacobian.Height(); ++row)
            {
               normal_projection += jacobian(row, column)
                                    * face_normal[row] / face_scale;
            }
            normal_width = std::max(normal_width, std::abs(normal_projection));
         }
         for (int i = 0; i < jacobian.Height(); ++i)
         {
            for (int j = 0; j < jacobian.Width(); ++j)
            {
               diameter_squared += jacobian(i, j) * jacobian(i, j);
            }
         }
         MFEM_VERIFY(normal_width > 0.0, "invalid DG normal cell width");
         return std::pair<double, double>(
            normal_width, std::sqrt(diameter_squared));
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
                           const std::filesystem::path &path,
                           const int subdivisions = subcells)
{
   const int rank = Mpi::WorldRank();
   const int gx_count = nx * subdivisions;
   const int gy_count = ny * subdivisions;
   const int gz_count = nz * subdivisions;
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
      for (int sx = 0; sx < subdivisions; ++sx)
      {
         for (int sy = 0; sy < subdivisions; ++sy)
         {
            for (int sz = 0; sz < subdivisions; ++sz)
            {
               double average = 0.0;
               for (int i = 0; i < 3; ++i)
               {
                  for (int j = 0; j < 3; ++j)
                  {
                     for (int k = 0; k < 3; ++k)
                     {
                        IntegrationPoint point;
                        point.Set3((sx + q[i]) / subdivisions,
                                   (sy + q[j]) / subdivisions,
                                   (sz + q[k]) / subdivisions);
                        average += w[i] * w[j] * w[k]
                                   * field.GetValue(element, point);
                     }
                  }
               }
               const int gx = ix * subdivisions + sx;
               const int gy = iy * subdivisions + sy;
               const int gz = iz * subdivisions + sz;
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

void ExportAlignedCommonAverages(const ParGridFunction &field,
                                 const std::filesystem::path &path)
{
   constexpr int counts[3] = {180, 216, 216};
   constexpr double origins[3] = {x_min, y_min, z_min};
   constexpr double lengths[3] = {x_max - x_min, y_max - y_min, z_max - z_min};
   const std::size_t total = static_cast<std::size_t>(counts[0]) * counts[1] * counts[2];
   std::vector<double> local(total, 0.0);
   std::vector<std::uint8_t> local_coverage(total, 0);
   const double q[3] = {0.5 * (1.0 - std::sqrt(3.0 / 5.0)), 0.5,
                        0.5 * (1.0 + std::sqrt(3.0 / 5.0))};
   const double w[3] = {5.0 / 18.0, 8.0 / 18.0, 5.0 / 18.0};
   ParFiniteElementSpace *space = field.ParFESpace();
   for (int element = 0; element < space->GetNE(); ++element)
   {
      ElementTransformation *transformation = space->GetElementTransformation(element);
      IntegrationPoint start, end;
      start.Set3(0.0, 0.0, 0.0); end.Set3(1.0, 1.0, 1.0);
      Vector low(3), high(3);
      transformation->Transform(start, low);
      transformation->Transform(end, high);
      int first[3], span[3];
      double mapped_low[3], mapped_high[3];
      for (int axis = 0; axis < 3; ++axis)
      {
         mapped_low[axis] = (low[axis] - origins[axis])
                            * counts[axis] / lengths[axis];
         mapped_high[axis] = (high[axis] - origins[axis])
                             * counts[axis] / lengths[axis];
      }
      bool fine_cell = true;
      for (int axis = 0; axis < 3; ++axis)
      {
         fine_cell &= std::abs(mapped_high[axis] - mapped_low[axis] - 0.5) < 1.0e-8;
      }
      if (fine_cell)
      {
         int voxel[3];
         for (int axis = 0; axis < 3; ++axis)
         {
            const double twice_low = 2.0 * mapped_low[axis];
            MFEM_VERIFY(std::abs(twice_low - std::round(twice_low)) < 1.0e-8,
                        "fine AMR cell is not aligned with the conservative common grid");
            voxel[axis] = static_cast<int>(std::floor(mapped_low[axis] + 1.0e-8));
            MFEM_VERIFY(voxel[axis] >= 0 && voxel[axis] < counts[axis]
                        && mapped_high[axis] <= voxel[axis] + 1.0 + 1.0e-8,
                        "fine AMR cell crosses a common-grid voxel boundary");
         }
         double average = 0.0;
         for (int a = 0; a < 3; ++a)
         for (int b = 0; b < 3; ++b)
         for (int c = 0; c < 3; ++c)
         {
            IntegrationPoint point;
            point.Set3(q[a], q[b], q[c]);
            average += w[a] * w[b] * w[c] * field.GetValue(element, point);
         }
         const std::size_t index =
            (static_cast<std::size_t>(voxel[0]) * counts[1] + voxel[1])
            * counts[2] + voxel[2];
         local[index] += average / 8.0;
         ++local_coverage[index];
         continue;
      }
      for (int axis = 0; axis < 3; ++axis)
      {
         first[axis] = static_cast<int>(std::lround(mapped_low[axis]));
         span[axis] = static_cast<int>(std::lround(mapped_high[axis])) - first[axis];
         MFEM_VERIFY(std::abs(mapped_low[axis] - first[axis]) < 1.0e-8
                     && std::abs(mapped_high[axis] - first[axis] - span[axis]) < 1.0e-8
                     && span[axis] > 0 && first[axis] >= 0
                     && first[axis] + span[axis] <= counts[axis],
                     "AMR element is not aligned with the conservative common grid");
      }
      for (int i = 0; i < span[0]; ++i)
      for (int j = 0; j < span[1]; ++j)
      for (int k = 0; k < span[2]; ++k)
      {
         double average = 0.0;
         for (int a = 0; a < 3; ++a)
         for (int b = 0; b < 3; ++b)
         for (int c = 0; c < 3; ++c)
         {
            IntegrationPoint point;
            point.Set3((i + q[a]) / span[0], (j + q[b]) / span[1],
                       (k + q[c]) / span[2]);
            average += w[a] * w[b] * w[c] * field.GetValue(element, point);
         }
         const std::size_t index =
            (static_cast<std::size_t>(first[0] + i) * counts[1] + first[1] + j)
            * counts[2] + first[2] + k;
         local[index] += average;
         local_coverage[index] += 8;
      }
   }
   std::vector<double> global(Mpi::WorldRank() == 0 ? total : 0);
   std::vector<std::uint8_t> global_coverage(Mpi::WorldRank() == 0 ? total : 0);
   MPI_Reduce(local.data(), Mpi::WorldRank() == 0 ? global.data() : nullptr,
              static_cast<int>(total), MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
   MPI_Reduce(local_coverage.data(),
              Mpi::WorldRank() == 0 ? global_coverage.data() : nullptr,
              static_cast<int>(total), MPI_UNSIGNED_CHAR, MPI_SUM, 0, MPI_COMM_WORLD);
   if (Mpi::WorldRank() == 0)
   {
      MFEM_VERIFY(std::all_of(global_coverage.begin(), global_coverage.end(),
                             [](std::uint8_t count) { return count == 8; }),
                  "AMR common-grid export has an uncovered or multiply covered voxel");
      std::ofstream output(path, std::ios::binary);
      MFEM_VERIFY(output.good(), "could not open AMR common-grid export");
      output.write(reinterpret_cast<const char *>(global.data()),
                   static_cast<std::streamsize>(total * sizeof(double)));
   }
}

void LoadGlobalNodalField(ParFiniteElementSpace &space, ParGridFunction &field,
                          const int nx, const int ny, const int nz,
                          const std::filesystem::path &path)
{
   const std::size_t count = static_cast<std::size_t>(nx) * ny * nz * 27;
   std::vector<double> values(count);
   if (Mpi::WorldRank() == 0)
   {
      std::ifstream input(path, std::ios::binary);
      MFEM_VERIFY(input.good(), "could not open shared mature initial state");
      input.read(reinterpret_cast<char *>(values.data()),
                 static_cast<std::streamsize>(count * sizeof(double)));
      MFEM_VERIFY(input.gcount() == static_cast<std::streamsize>(count * sizeof(double)),
                  "shared mature initial state has the wrong size");
   }
   MPI_Bcast(values.data(), static_cast<int>(count), MPI_DOUBLE, 0, MPI_COMM_WORLD);
   field = 0.0;
   Array<int> dofs;
   for (int element = 0; element < space.GetNE(); ++element)
   {
      ElementTransformation *transformation = space.GetElementTransformation(element);
      int ix, iy, iz;
      CellIndexAndOrigin(*transformation, nx, ny, nz, ix, iy, iz);
      const IntegrationRule &nodes = space.GetFE(element)->GetNodes();
      Vector local(nodes.GetNPoints());
      for (int q = 0; q < nodes.GetNPoints(); ++q)
      {
         const auto &point = nodes.IntPoint(q);
         const int i = std::clamp(static_cast<int>(std::lround(2.0 * point.x)), 0, 2);
         const int j = std::clamp(static_cast<int>(std::lround(2.0 * point.y)), 0, 2);
         const int k = std::clamp(static_cast<int>(std::lround(2.0 * point.z)), 0, 2);
         const std::size_t index = (((static_cast<std::size_t>(ix) * ny + iy) * nz + iz)
                                    * 3 + i) * 9 + j * 3 + k;
         local[q] = values[index];
      }
      space.GetElementVDofs(element, dofs);
      field.SetSubVector(dofs, local);
   }
}

int RefineMarkedBackground(Mesh &mesh, const int nx, const int ny, const int nz,
                           const std::filesystem::path &path)
{
   const std::size_t count = static_cast<std::size_t>(nx) * ny * nz;
   std::vector<std::uint8_t> flags(count);
   std::ifstream input(path, std::ios::binary);
   MFEM_VERIFY(input.good(), "could not open replay-derived AMR marks");
   input.read(reinterpret_cast<char *>(flags.data()),
              static_cast<std::streamsize>(count));
   MFEM_VERIFY(input.gcount() == static_cast<std::streamsize>(count),
               "AMR mark file size does not match base mesh");
   MFEM_VERIFY(input.peek() == EOF, "AMR mark file has extra bytes");
   Array<int> marked;
   IntegrationPoint midpoint;
   midpoint.Set3(0.5, 0.5, 0.5);
   for (int element = 0; element < mesh.GetNE(); ++element)
   {
      Vector x(3);
      mesh.GetElementTransformation(element)->Transform(midpoint, x);
      const int ix = std::clamp(static_cast<int>(std::floor((x[0] - x_min)
                           * nx / (x_max - x_min))), 0, nx - 1);
      const int iy = std::clamp(static_cast<int>(std::floor((x[1] - y_min)
                           * ny / (y_max - y_min))), 0, ny - 1);
      const int iz = std::clamp(static_cast<int>(std::floor((x[2] - z_min)
                           * nz / (z_max - z_min))), 0, nz - 1);
      if (flags[(static_cast<std::size_t>(ix) * ny + iy) * nz + iz])
      {
         marked.Append(element);
      }
   }
   mesh.EnsureNCMesh(true);
   mesh.GeneralRefinement(marked, 1);
   return marked.Size();
}

int RefineMarkedChildren(Mesh &mesh, const int nx, const int ny, const int nz,
                         const int level, const std::filesystem::path &path)
{
   const int factor = 1 << level;
   const int counts[3] = {factor * nx, factor * ny, factor * nz};
   const double origins[3] = {x_min, y_min, z_min};
   const double lengths[3] = {x_max - x_min, y_max - y_min, z_max - z_min};
   const std::size_t count = static_cast<std::size_t>(counts[0]) * counts[1] * counts[2];
   std::vector<std::uint8_t> flags(count);
   std::ifstream input(path, std::ios::binary);
   MFEM_VERIFY(input.good(), "could not open nested AMR marks");
   input.read(reinterpret_cast<char *>(flags.data()), static_cast<std::streamsize>(count));
   MFEM_VERIFY(input.gcount() == static_cast<std::streamsize>(count) && input.peek() == EOF,
               "nested AMR mark file size is invalid");
   Array<int> marked;
   IntegrationPoint start, end, midpoint;
   start.Set3(0.0, 0.0, 0.0);
   end.Set3(1.0, 1.0, 1.0);
   midpoint.Set3(0.5, 0.5, 0.5);
   for (int element = 0; element < mesh.GetNE(); ++element)
   {
      auto *transformation = mesh.GetElementTransformation(element);
      Vector low(3), high(3), center(3);
      transformation->Transform(start, low);
      transformation->Transform(end, high);
      transformation->Transform(midpoint, center);
      int index[3];
      bool target_level_child = true;
      for (int axis = 0; axis < 3; ++axis)
      {
         const double width = lengths[axis] / counts[axis];
         target_level_child &= std::abs((high[axis] - low[axis]) / width - 1.0) < 1.0e-8;
         index[axis] = std::clamp(
            static_cast<int>(std::floor((center[axis] - origins[axis]) / width)),
            0, counts[axis] - 1);
      }
      const std::size_t flat = (static_cast<std::size_t>(index[0]) * counts[1]
                                + index[1]) * counts[2] + index[2];
      if (target_level_child && flags[flat]) { marked.Append(element); }
   }
   mesh.GeneralRefinement(marked, 1, 1);
   return marked.Size();
}

double FieldMass(const ParGridFunction &field)
{
   double local = 0.0;
   ParFiniteElementSpace *space = field.ParFESpace();
   const IntegrationRule &rule = IntRules.Get(Geometry::CUBE, 6);
   for (int element = 0; element < space->GetNE(); ++element)
   {
      ElementTransformation *transformation = space->GetElementTransformation(element);
      for (int q = 0; q < rule.GetNPoints(); ++q)
      {
         const IntegrationPoint &point = rule.IntPoint(q);
         transformation->SetIntPoint(&point);
         local += point.weight * transformation->Weight()
                  * field.GetValue(element, point);
      }
   }
   double global = 0.0;
   MPI_Allreduce(&local, &global, 1, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
   return global;
}

double FieldL1Difference(const ParGridFunction &first,
                         const ParGridFunction &second)
{
   double local = 0.0;
   ParFiniteElementSpace *space = first.ParFESpace();
   const IntegrationRule &rule = IntRules.Get(Geometry::CUBE, 7);
   for (int element = 0; element < space->GetNE(); ++element)
   {
      ElementTransformation *transformation = space->GetElementTransformation(element);
      for (int q = 0; q < rule.GetNPoints(); ++q)
      {
         const IntegrationPoint &point = rule.IntPoint(q);
         transformation->SetIntPoint(&point);
         local += point.weight * transformation->Weight()
                  * std::abs(first.GetValue(element, point)
                             - second.GetValue(element, point));
      }
   }
   double global = 0.0;
   MPI_Allreduce(&local, &global, 1, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
   return global;
}

int RepairCellAverages(ParFiniteElementSpace &space, ParGridFunction &field)
{
   const double weights[3] = {1.0 / 6.0, 2.0 / 3.0, 1.0 / 6.0};
   std::vector<double> averages(space.GetNE());
   std::vector<double> cell_volumes(space.GetNE());
   Array<int> dofs;
   int local_negative = 0;
   double local_sum = 0.0, local_maximum = 0.0;
   for (int element = 0; element < space.GetNE(); ++element)
   {
      double average = 0.0;
      for (int i = 0; i < 3; ++i)
      for (int j = 0; j < 3; ++j)
      for (int k = 0; k < 3; ++k)
      {
         IntegrationPoint point;
         point.Set3(0.5 * i, 0.5 * j, 0.5 * k);
         average += weights[i] * weights[j] * weights[k]
                    * field.GetValue(element, point);
      }
      averages[element] = average;
      IntegrationPoint center;
      center.Set3(0.5, 0.5, 0.5);
      ElementTransformation *transformation = space.GetElementTransformation(element);
      transformation->SetIntPoint(&center);
      cell_volumes[element] = transformation->Weight();
      local_sum += cell_volumes[element] * average;
      local_maximum = std::max(local_maximum, average);
      local_negative += average < 0.0 ? 1 : 0;
   }
   double target = 0.0, upper = 0.0;
   MPI_Allreduce(&local_sum, &target, 1, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
   MPI_Allreduce(&local_maximum, &upper, 1, MPI_DOUBLE, MPI_MAX, MPI_COMM_WORLD);
   double lower = 0.0;
   for (int iteration = 0; iteration < 100; ++iteration)
   {
      const double lambda = 0.5 * (lower + upper);
      double local_projected_sum = 0.0, projected_sum = 0.0;
      for (int element = 0; element < space.GetNE(); ++element)
      {
         local_projected_sum += cell_volumes[element]
                                * std::max(averages[element] - lambda, 0.0);
      }
      MPI_Allreduce(&local_projected_sum, &projected_sum, 1, MPI_DOUBLE,
                    MPI_SUM, MPI_COMM_WORLD);
      if (projected_sum > target) { lower = lambda; }
      else { upper = lambda; }
   }
   const double lambda = 0.5 * (lower + upper);
   for (int element = 0; element < space.GetNE(); ++element)
   {
      const double target_average = std::max(averages[element] - lambda, 0.0);
      const double shift = target_average - averages[element];
      space.GetElementVDofs(element, dofs);
      Vector values(dofs.Size());
      field.GetSubVector(dofs, values);
      if (target_average == 0.0) { values = 0.0; }
      else { values += shift; }
      field.SetSubVector(dofs, values);
   }
   int global_negative = 0;
   MPI_Allreduce(&local_negative, &global_negative, 1, MPI_INT, MPI_SUM,
                 MPI_COMM_WORLD);
   return global_negative;
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

      // Eliminate the average equality with an orthonormal Householder basis,
      // matching the reduced incumbent QP. Deduplicate shared subcell-face
      // Bernstein rows before constructing the fixed OSQP matrices.
      double average_norm = 0.0;
      for (double value : average) { average_norm += value * value; }
      average_norm = std::sqrt(average_norm);
      std::array<double, variables> householder{};
      householder[variables - 1] = 1.0;
      for (int i = 0; i < variables; ++i)
      {
         householder[i] -= average[i] / average_norm;
      }
      double householder_norm_squared = 0.0;
      for (double value : householder) { householder_norm_squared += value * value; }
      null_basis.assign(variables * reduced_variables, 0.0);
      for (int row = 0; row < variables; ++row)
      for (int column = 0; column < reduced_variables; ++column)
      {
         null_basis[row * reduced_variables + column] =
            (row == column ? 1.0 : 0.0)
            - 2.0 * householder[row] * householder[column]
              / householder_norm_squared;
      }
      for (int row = 0; row < bernstein_rows; ++row)
      {
         bool duplicate = false;
         for (int kept = 0; kept < unique_rows && !duplicate; ++kept)
         {
            duplicate = true;
            for (int column = 0; column < variables; ++column)
            {
               if (std::abs(constraints[row * variables + column]
                            - unique_constraints[kept * variables + column]) > 5.0e-15)
               {
                  duplicate = false;
                  break;
               }
            }
         }
         if (!duplicate)
         {
            unique_constraints.insert(unique_constraints.end(),
               constraints.begin() + row * variables,
               constraints.begin() + (row + 1) * variables);
            ++unique_rows;
         }
      }
      reduced_hessian.assign(reduced_variables * reduced_variables, 0.0);
      reduced_constraints.assign(unique_rows * reduced_variables, 0.0);
      for (int i = 0; i < reduced_variables; ++i)
      for (int j = 0; j < reduced_variables; ++j)
      for (int a = 0; a < variables; ++a)
      for (int b = 0; b < variables; ++b)
      {
         reduced_hessian[i * reduced_variables + j] +=
            null_basis[a * reduced_variables + i] * hessian[a * variables + b]
            * null_basis[b * reduced_variables + j];
      }
      for (int row = 0; row < unique_rows; ++row)
      for (int column = 0; column < reduced_variables; ++column)
      for (int i = 0; i < variables; ++i)
      {
         reduced_constraints[row * reduced_variables + column] +=
            unique_constraints[row * variables + i]
            * null_basis[i * reduced_variables + column];
      }

      // OSQP stores the upper Hessian triangle and constraint matrix in CSC.
      p_columns.resize(reduced_variables + 1);
      for (int column = 0; column < reduced_variables; ++column)
      {
         p_columns[column] = static_cast<OSQPInt>(p_values.size());
         for (int row = 0; row <= column; ++row)
         {
            p_rows.push_back(row);
            p_values.push_back(reduced_hessian[row * reduced_variables + column]);
         }
      }
      p_columns[reduced_variables] = static_cast<OSQPInt>(p_values.size());
      a_columns.resize(reduced_variables + 1);
      for (int column = 0; column < reduced_variables; ++column)
      {
         a_columns[column] = static_cast<OSQPInt>(a_values.size());
         for (int row = 0; row < unique_rows; ++row)
         {
            a_rows.push_back(row);
            a_values.push_back(reduced_constraints[row * reduced_variables + column]);
         }
      }
      a_columns[reduced_variables] = static_cast<OSQPInt>(a_values.size());
      q.assign(reduced_variables, 0.0);
      lower.assign(unique_rows, 0.0);
      upper.assign(unique_rows, OSQP_INFTY);
      P = OSQPCscMatrix_new(reduced_variables, reduced_variables, p_values.size(),
                            p_values.data(), p_rows.data(), p_columns.data());
      A = OSQPCscMatrix_new(unique_rows, reduced_variables, a_values.size(),
                            a_values.data(), a_rows.data(), a_columns.data());
      settings = OSQPSettings_new();
      settings->verbose = 0;
      settings->warm_starting = 1;
      settings->polishing = 1;
      settings->eps_abs = 1.0e-11;
      settings->eps_rel = 1.0e-11;
      settings->max_iter = 10000;
      const OSQPInt error = osqp_setup(
         &solver, P, q.data(), A, lower.data(), upper.data(), unique_rows,
         reduced_variables, settings);
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
      last_qp = false;
      last_zero_average = false;
      last_certified = false;
      double cell_average = 0.0;
      for (int i = 0; i < variables; ++i) { cell_average += average[i] * raw[i]; }
      MFEM_VERIFY(cell_average >= -1.0e-12,
                  "corrected-step diagnostic encountered a negative cell average");
      if (cell_average <= 0.0)
      {
         result.fill(0.0);
         last_zero_average = true;
         last_certified = true;
         return true;
      }
      std::array<double, variables> normalized{};
      double minimum = OSQP_INFTY;
      for (int i = 0; i < variables; ++i) { normalized[i] = raw[i] / cell_average; }
      if (AdaptiveCertificate(raw))
      {
         result = raw;
         last_certified = true;
         return false;
      }
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
         last_certified = true;
         return false;
      }
      last_qp = true;
      for (int row = 0; row < unique_rows; ++row)
      {
         lower[row] = positivity_margin;
         for (int column = 0; column < variables; ++column)
         {
            lower[row] -= unique_constraints[row * variables + column]
                          * normalized[column];
         }
      }
      MFEM_VERIFY(osqp_update_data_vec(solver, nullptr, lower.data(), nullptr) == 0,
                  "OSQP local-Q2 bound update failed");
      // Match the incumbent projector: start each independent cell problem
      // from its own feasible contraction toward the unit-average constant.
      // Reusing the previous spatial cell is unreliable in near-vacuum tails.
      const double theta = std::clamp(
         (1.0 - positivity_margin) / (1.0 - minimum), 0.0, 1.0);
      std::array<OSQPFloat, reduced_variables> primal_start{};
      std::vector<OSQPFloat> dual_start(unique_rows, 0.0);
      for (int column = 0; column < reduced_variables; ++column)
      {
         for (int i = 0; i < variables; ++i)
         {
            const double scaling = 1.0 + theta * (normalized[i] - 1.0);
            primal_start[column] += null_basis[i * reduced_variables + column]
                                    * (scaling - normalized[i]);
         }
      }
      MFEM_VERIFY(osqp_warm_start(solver, primal_start.data(), dual_start.data()) == 0,
                  "OSQP local-Q2 warm start failed");
      MFEM_VERIFY(osqp_solve(solver) == 0, "OSQP local-Q2 solve failed");
      if (solver->info->status_val != OSQP_SOLVED
          && solver->info->status_val != OSQP_SOLVED_INACCURATE)
      {
         std::cerr << "OSQP status=" << solver->info->status
                   << " iterations=" << solver->info->iter
                   << " average=" << cell_average
                   << " normalized_minimum=" << minimum << std::endl;
      }
      MFEM_VERIFY(solver->info->status_val == OSQP_SOLVED
                  || solver->info->status_val == OSQP_SOLVED_INACCURATE,
                  "OSQP local-Q2 optimization did not converge");
      std::array<double, variables> candidate{};
      double candidate_average = 0.0;
      for (int i = 0; i < variables; ++i)
      {
         candidate[i] = normalized[i];
         for (int column = 0; column < reduced_variables; ++column)
         {
            candidate[i] += null_basis[i * reduced_variables + column]
                            * solver->solution->x[column];
         }
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
      double final_minimum = OSQP_INFTY;
      for (int row = 0; row < bernstein_rows; ++row)
      {
         double value = 0.0;
         for (int column = 0; column < variables; ++column)
         {
            value += constraints[row * variables + column] * candidate[column];
         }
         final_minimum = std::min(final_minimum, value);
      }
      last_certified = std::isfinite(final_minimum) && final_minimum >= 0.0;
      for (int i = 0; i < variables; ++i) { result[i] = cell_average * candidate[i]; }
      return true;
   }

   bool LastWasQp() const { return last_qp; }
   bool LastWasZeroAverage() const { return last_zero_average; }
   bool LastCertified() const { return last_certified; }

private:
   static constexpr int reduced_variables = 26;
   using BernsteinBox = std::array<double, 27>;

   static int Index(const int i, const int j, const int k)
   {
      return (i * 3 + j) * 3 + k;
   }

   static std::pair<BernsteinBox, BernsteinBox>
   SplitAxis(const BernsteinBox &box, const int axis)
   {
      BernsteinBox left{}, right{};
      for (int a = 0; a < 3; ++a)
      for (int b = 0; b < 3; ++b)
      {
         double v[3];
         for (int q = 0; q < 3; ++q)
         {
            const int i = axis == 0 ? q : a;
            const int j = axis == 1 ? q : (axis == 0 ? a : b);
            const int k = axis == 2 ? q : b;
            v[q] = box[Index(i, j, k)];
         }
         const double midpoint0 = 0.5 * (v[0] + v[1]);
         const double midpoint1 = 0.5 * (v[1] + v[2]);
         const double centre = 0.5 * (midpoint0 + midpoint1);
         const double lv[3] = {v[0], midpoint0, centre};
         const double rv[3] = {centre, midpoint1, v[2]};
         for (int q = 0; q < 3; ++q)
         {
            const int i = axis == 0 ? q : a;
            const int j = axis == 1 ? q : (axis == 0 ? a : b);
            const int k = axis == 2 ? q : b;
            left[Index(i, j, k)] = lv[q];
            right[Index(i, j, k)] = rv[q];
         }
      }
      return {left, right};
   }

   static bool AdaptiveCertificate(const std::array<double, 27> &nodal)
   {
      // Match PositivityLimiter.classify_coefficients: convert the physical
      // Q2 polynomial to whole-cell tensor Bernstein coefficients, then use
      // depth-four de Casteljau subdivision. A negative corner or box-centre
      // value is a physical witness and therefore prevents an adaptive skip.
      const double transform[3][3] = {
         {1.0, 0.0, 0.0},
         {-0.5, 2.0, -0.5},
         {0.0, 0.0, 1.0}
      };
      BernsteinBox root{};
      for (int a = 0; a < 3; ++a)
      for (int b = 0; b < 3; ++b)
      for (int c = 0; c < 3; ++c)
      for (int i = 0; i < 3; ++i)
      for (int j = 0; j < 3; ++j)
      for (int k = 0; k < 3; ++k)
      {
         root[Index(a, b, c)] += transform[a][i] * transform[b][j]
                                    * transform[c][k] * nodal[Index(i, j, k)];
      }
      std::vector<std::pair<BernsteinBox, int>> stack{{root, 0}};
      bool unresolved = false;
      while (!stack.empty())
      {
         auto [box, depth] = std::move(stack.back());
         stack.pop_back();
         const auto [minimum_it, maximum_it] =
            std::minmax_element(box.begin(), box.end());
         const double scale = std::max(std::abs(*minimum_it), std::abs(*maximum_it));
         const double witness_tolerance = 128.0 * std::numeric_limits<double>::epsilon()
                                          * std::max(scale, std::numeric_limits<double>::min());
         double witness = OSQP_INFTY;
         for (const int i : {0, 2})
         for (const int j : {0, 2})
         for (const int k : {0, 2})
         {
            witness = std::min(witness, box[Index(i, j, k)]);
         }
         double centre = 0.0;
         const double weights[3] = {0.25, 0.5, 0.25};
         for (int i = 0; i < 3; ++i)
         for (int j = 0; j < 3; ++j)
         for (int k = 0; k < 3; ++k)
         {
            centre += weights[i] * weights[j] * weights[k] * box[Index(i, j, k)];
         }
         witness = std::min(witness, centre);
         if (witness < -witness_tolerance) { return false; }
         if (*minimum_it >= 0.0) { continue; }
         if (depth >= 4)
         {
            unresolved = true;
            continue;
         }
         std::vector<BernsteinBox> children{box};
         for (int axis = 0; axis < 3; ++axis)
         {
            std::vector<BernsteinBox> next;
            next.reserve(children.size() * 2);
            for (const auto &child : children)
            {
               auto split = SplitAxis(child, axis);
               next.push_back(std::move(split.first));
               next.push_back(std::move(split.second));
            }
            children = std::move(next);
         }
         for (auto &child : children)
         {
            stack.emplace_back(std::move(child), depth + 1);
         }
      }
      return !unresolved;
   }

   static constexpr double positivity_margin = 1.0e-12;
   int unique_rows = 0;
   std::vector<double> hessian, average, constraints, null_basis,
                       unique_constraints, reduced_hessian, reduced_constraints;
   std::vector<OSQPFloat> p_values, a_values, q, lower, upper;
   std::vector<OSQPInt> p_rows, p_columns, a_rows, a_columns;
   OSQPCscMatrix *P = nullptr;
   OSQPCscMatrix *A = nullptr;
   OSQPSettings *settings = nullptr;
   OSQPSolver *solver = nullptr;
   bool last_qp = false;
   bool last_zero_average = false;
   bool last_certified = false;
};

struct ProjectionCounts
{
   int modified = 0;
   int qp = 0;
   int zero_average = 0;
   int certified = 0;
};

ProjectionCounts ProjectField(LocalQ2Projector &projector,
                              ParFiniteElementSpace &space,
                              const ParGridFunction &raw,
                              ParGridFunction &corrected)
{
   corrected = 0.0;
   ProjectionCounts local{};
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
      local.modified += projector.Project(nodal, projected) ? 1 : 0;
      local.qp += projector.LastWasQp() ? 1 : 0;
      local.zero_average += projector.LastWasZeroAverage() ? 1 : 0;
      local.certified += projector.LastCertified() ? 1 : 0;
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
   const int local_values[4] = {
      local.modified, local.qp, local.zero_average, local.certified
   };
   int global_values[4] = {};
   MPI_Allreduce(local_values, global_values, 4, MPI_INT, MPI_SUM, MPI_COMM_WORLD);
   return {global_values[0], global_values[1], global_values[2], global_values[3]};
}
}

namespace
{
struct FaceProbeResult
{
   std::array<double, 3> actions{};
   std::array<double, 3> constant_test_actions{};
   double diffusion_constant_maximum = 0.0;
   int cells = 0;
};

FaceProbeResult NonconformingFaceActions(const bool refine_right,
                                         const bool uniformly_refined,
                                         const int test)
{
   Mesh serial = Mesh::MakeCartesian3D(
      uniformly_refined ? 4 : 2, uniformly_refined ? 2 : 1,
      uniformly_refined ? 2 : 1, Element::HEXAHEDRON,
      x_max - x_min, y_max - y_min, z_max - z_min);
   for (int vertex = 0; vertex < serial.GetNV(); ++vertex)
   {
      double *x = serial.GetVertex(vertex);
      x[0] += x_min; x[1] += y_min; x[2] += z_min;
   }
   if (refine_right)
   {
      serial.EnsureNCMesh(true);
      Array<int> marked(1);
      marked[0] = 1;
      serial.GeneralRefinement(marked, 1);
   }
   ParMesh mesh(MPI_COMM_WORLD, serial);
   int local_cells = mesh.GetNE();
   FaceProbeResult probe;
   MPI_Allreduce(&local_cells, &probe.cells, 1, MPI_INT, MPI_SUM, MPI_COMM_WORLD);
   L2_FECollection collection(2, 3, BasisType::GaussLobatto);
   ParFiniteElementSpace space(&mesh, &collection);
   LorenzDrift drift;
   DenseMatrix tensor(3);
   tensor = 0.0;
   tensor(0, 0) = 1.0; tensor(0, 1) = 0.4; tensor(0, 2) = 0.2;
   tensor(1, 0) = 0.4; tensor(1, 1) = 1.0; tensor(1, 2) = 0.3;
   tensor(2, 0) = 0.2; tensor(2, 1) = 0.3; tensor(2, 2) = 1.0;
   tensor *= -1.0;
   MatrixConstantCoefficient diffusion(tensor);

   ParBilinearForm complete(&space);
   auto *volume = new ConservativeConvectionIntegrator(drift, -1.0);
   volume->SetIntRule(&IntRules.Get(Geometry::CUBE, 6));
   complete.AddDomainIntegrator(volume);
   auto *face = new DGTraceIntegrator(drift, -1.0, -0.5);
   face->SetIntRule(&IntRules.Get(Geometry::SQUARE, 14));
   complete.AddInteriorFaceIntegrator(face);
   complete.AddDomainIntegrator(new DiffusionIntegrator(diffusion));
   complete.AddInteriorFaceIntegrator(new DolfinxPenaltyDGDiffusionIntegrator(
      diffusion, -1.0, 64.0));
   complete.Assemble(); complete.Finalize();

   ParBilinearForm advection_face(&space);
   auto *advective_flux = new DGTraceIntegrator(drift, -1.0, -0.5);
   advective_flux->SetIntRule(&IntRules.Get(Geometry::SQUARE, 14));
   advection_face.AddInteriorFaceIntegrator(advective_flux);
   advection_face.Assemble(); advection_face.Finalize();

   ParBilinearForm diffusion_face(&space);
   diffusion_face.AddInteriorFaceIntegrator(new DolfinxPenaltyDGDiffusionIntegrator(
      diffusion, -1.0, 64.0));
   diffusion_face.Assemble(); diffusion_face.Finalize();

   FunctionCoefficient smooth([test](const Vector &x) {
      if (test == 1)
      {
         return 1.0 + 0.003 * x[0] - 0.002 * x[1] + 0.001 * x[2]
                + 0.00004 * x[0] * x[1] + 0.00003 * x[2] * x[2];
      }
      return 1.0 + 0.003 * x[0] - 0.002 * x[1] + 0.001 * x[2];
   });
   ParGridFunction trial(&space), jump(&space), constant(&space);
   trial.ProjectCoefficient(smooth);
   if (test == 2)
   {
      Array<int> local_dofs;
      for (int element = 0; element < space.GetNE(); ++element)
      {
         ElementTransformation *transformation = space.GetElementTransformation(element);
         IntegrationPoint midpoint;
         midpoint.Set3(0.5, 0.5, 0.5);
         Vector x(3);
         transformation->Transform(midpoint, x);
         space.GetElementVDofs(element, local_dofs);
         Vector values(local_dofs.Size());
         values = x[0] < 0.0 ? 1.0 : 2.0;
         trial.SetSubVector(local_dofs, values);
      }
   }
   constant = 1.0;
   jump = 0.0;
   Array<int> dofs;
   for (int element = 0; element < space.GetNE(); ++element)
   {
      ElementTransformation *transformation = space.GetElementTransformation(element);
      IntegrationPoint midpoint;
      midpoint.Set3(0.5, 0.5, 0.5);
      Vector x(3);
      transformation->Transform(midpoint, x);
      space.GetElementVDofs(element, dofs);
      Vector values(dofs.Size());
      values = x[0] < 0.0 ? 2.0 : -1.0;
      jump.SetSubVector(dofs, values);
   }
   Vector u, v, one;
   trial.GetTrueDofs(u); jump.GetTrueDofs(v); constant.GetTrueDofs(one);
   ParBilinearForm *forms[] = {&complete, &advection_face, &diffusion_face};
   for (int i = 0; i < 3; ++i)
   {
      HypreParMatrix *matrix = forms[i]->ParallelAssemble();
      Vector result(matrix->Height());
      matrix->Mult(u, result);
      const double local = v * result;
      MPI_Allreduce(&local, &probe.actions[i], 1, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
      const double local_constant_action = one * result;
      MPI_Allreduce(&local_constant_action, &probe.constant_test_actions[i],
                    1, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
      if (i == 2)
      {
         Vector diffusion_constant(matrix->Height());
         matrix->Mult(one, diffusion_constant);
         const double local_maximum = diffusion_constant.Normlinf();
         MPI_Allreduce(&local_maximum, &probe.diffusion_constant_maximum,
                       1, MPI_DOUBLE, MPI_MAX, MPI_COMM_WORLD);
      }
      delete matrix;
   }
   return probe;
}

int RunNonconformingFaceProbe(const std::filesystem::path &output)
{
   std::array<FaceProbeResult, 3> nc;
   std::array<FaceProbeResult, 2> uniform;
   std::array<std::array<double, 3>, 2> relative{};
   for (int test = 0; test < 3; ++test)
   {
      nc[test] = NonconformingFaceActions(true, false, test);
      if (test < 2)
      {
         uniform[test] = NonconformingFaceActions(false, true, test);
         for (int i = 0; i < 3; ++i)
         {
            relative[test][i] = std::abs(nc[test].actions[i]
                                          - uniform[test].actions[i])
               / std::max(1.0, std::abs(uniform[test].actions[i]));
         }
      }
   }
   double maximum_relative = 0.0, maximum_conservation = 0.0;
   double maximum_constant_diffusion = 0.0;
   for (const auto &test : relative)
   for (double value : test) { maximum_relative = std::max(maximum_relative, value); }
   for (const auto &test : nc)
   {
      maximum_constant_diffusion = std::max(maximum_constant_diffusion,
                                            test.diffusion_constant_maximum);
      for (double value : test.constant_test_actions)
      {
         maximum_conservation = std::max(maximum_conservation, std::abs(value));
      }
   }
   const bool pass = nc[0].cells == 9 && uniform[0].cells == 16
                     && maximum_relative < 1.0e-9
                     && maximum_conservation < 1.0e-8
                     && maximum_constant_diffusion < 1.0e-10;
   if (Mpi::WorldRank() == 0)
   {
      std::ofstream report(output);
      report << std::setprecision(17)
             << "{\n  \"status\": \"" << (pass ? "PASS" : "FAIL") << "\",\n"
             << "  \"nc_cells\": " << nc[0].cells << ",\n"
             << "  \"uniform_cells\": " << uniform[0].cells << ",\n"
             << "  \"tested_states\": [\"affine\", \"quadratic\", \"discontinuous\"],\n"
             << "  \"relative_action_errors\": [["
             << relative[0][0] << ", " << relative[0][1] << ", " << relative[0][2]
             << "], [" << relative[1][0] << ", " << relative[1][1] << ", "
             << relative[1][2] << "]],\n"
             << "  \"maximum_relative_action_error\": " << maximum_relative << ",\n"
             << "  \"maximum_constant_test_action\": " << maximum_conservation << ",\n"
             << "  \"discontinuous_nc_actions\": [" << nc[2].actions[0] << ", "
             << nc[2].actions[1] << ", " << nc[2].actions[2] << "],\n"
             << "  \"maximum_diffusion_action_on_constant\": "
             << maximum_constant_diffusion << "\n}\n";
   }
   return pass ? 0 : 2;
}
}

int main(int argc, char *argv[])
{
   Mpi::Init(argc, argv);
   const int rank = Mpi::WorldRank();
   if (argc == 3 && std::string(argv[1]) == "nc-face-probe")
   {
      return RunNonconformingFaceProbe(argv[2]);
   }
   const bool mature_mode = argc == 7 && std::string(argv[1]) == "mature";
   const bool amr_mode = (argc == 8 || argc == 9) && std::string(argv[1]) == "amr";
   const bool amr2_mode = (argc == 9 || argc == 10) && std::string(argv[1]) == "amr2";
   const bool amr3_mode = (argc == 10 || argc == 11) && std::string(argv[1]) == "amr3";
   const bool adaptive_mode = amr_mode || amr2_mode || amr3_mode;
   MFEM_VERIFY(argc == 5 || mature_mode || adaptive_mode,
               "usage: mfem_physical_equivalence [mature|amr|amr2|amr3] NX NY NZ [INPUTS] OUTPUT_DIRECTORY");
   const int offset = (mature_mode || adaptive_mode) ? 1 : 0;
   const int nx = std::stoi(argv[1 + offset]);
   const int ny = std::stoi(argv[2 + offset]);
   const int nz = std::stoi(argv[3 + offset]);
   // FFCx selects these effective Gauss orders for the frozen combined form
   // and for the isolated diagnostic form, respectively.  The upwind switch
   // makes the face integrand piecewise polynomial, so matching the actual
   // incumbent quadrature is part of operator equivalence.
   constexpr int combined_face_quadrature_order = 14;
   constexpr int isolated_advection_face_quadrature_order = 12;
   const std::filesystem::path initial_path = mature_mode ? argv[5] : "";
   const std::filesystem::path mark_path = adaptive_mode ? argv[5] : "";
   const std::filesystem::path second_mark_path = (amr2_mode || amr3_mode) ? argv[6] : "";
   const std::filesystem::path third_mark_path = amr3_mode ? argv[7] : "";
   const std::filesystem::path mixture_path =
      amr3_mode ? argv[8] : (amr2_mode ? argv[7] : (amr_mode ? argv[6] : ""));
   const std::filesystem::path output_directory(
      amr3_mode ? argv[9] : (amr2_mode ? argv[8] : (amr_mode ? argv[7] :
                    (mature_mode ? argv[6] : argv[4]))));
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
   const int requested_refinements = adaptive_mode
      ? RefineMarkedBackground(serial, nx, ny, nz, mark_path) : 0;
   const int requested_child_refinements = (amr2_mode || amr3_mode)
      ? RefineMarkedChildren(serial, nx, ny, nz, 1, second_mark_path) : 0;
   const int requested_grandchild_refinements = amr3_mode
      ? RefineMarkedChildren(serial, nx, ny, nz, 2, third_mark_path) : 0;
   ParMesh mesh(MPI_COMM_WORLD, serial);
   int local_cells = mesh.GetNE(), global_cells = 0;
   MPI_Allreduce(&local_cells, &global_cells, 1, MPI_INT, MPI_SUM, MPI_COMM_WORLD);
   if (adaptive_mode && rank == 0)
   {
      std::cout << "static AMR mesh: " << global_cells << " cells from "
                << requested_refinements << " first-level and "
                << requested_child_refinements << " second-level and "
                << requested_grandchild_refinements << " third-level requested refinements"
                << std::endl;
   }
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

   if (mature_mode || adaptive_mode)
   {
      ParGridFunction state(&space);
      int initial_qp_cells = 0;
      int initial_uncertified_cells = 0;
      double initial_projection_correction = 0.0;
      if (adaptive_mode)
      {
         MatureGaussianMixture mixture(mixture_path);
         ParLinearForm load(&space);
         auto *integrator = new DomainLFIntegrator(mixture);
         integrator->SetIntRule(&IntRules.Get(Geometry::CUBE, 14));
         load.AddDomainIntegrator(integrator);
         load.Assemble();
         HypreParVector *rhs = load.ParallelAssemble();
         Vector projected(space.GetTrueVSize());
         mass_solver.Mult(*rhs, projected);
         state.SetFromTrueDofs(projected);
         delete rhs;
         const double raw_mass = FieldMass(state);
         MFEM_VERIFY(raw_mass > 0.0, "AMR initial mixture has nonpositive mass");
         state *= 1.0 / raw_mass;
         ParGridFunction raw(state);
         RepairCellAverages(space, state);
         ParGridFunction admissible(&space);
         const ProjectionCounts initial_projection =
            ProjectField(local_projector, space, state, admissible);
         initial_qp_cells = initial_projection.qp;
         initial_uncertified_cells = global_cells - initial_projection.certified;
         initial_projection_correction = FieldL1Difference(raw, admissible);
         state = admissible;
      }
      else
      {
         LoadGlobalNodalField(space, state, nx, ny, nz, initial_path);
      }
      const double initial_mass = FieldMass(state);
      if (adaptive_mode)
      {
         ExportAlignedCommonAverages(state,
            output_directory / "initial_q2_subcell_averages.bin");
      }
      else
      {
         ExportSubcellAverages(state, nx, ny, nz,
            output_directory / "initial_q2_subcell_averages.bin", 6);
      }
      const int steps = amr3_mode && argc == 11 ? std::stoi(argv[10])
                        : (amr2_mode && argc == 10 ? std::stoi(argv[9])
                        : (amr_mode && argc == 9 ? std::stoi(argv[8]) : 320));
      MFEM_VERIFY(steps > 0 && steps <= 320, "AMR diagnostic step count is invalid");
      std::vector<double> masses;
      std::vector<double> relative_corrections;
      std::vector<int> qp_cells;
      std::vector<int> zero_average_cells;
      std::vector<int> uncertified_cells;
      std::vector<int> repaired_negative_averages;
      masses.reserve(steps + 1);
      masses.push_back(initial_mass);

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

      const auto started = std::chrono::steady_clock::now();
      for (int step = 0; step < steps; ++step)
      {
         Vector current;
         state.GetTrueDofs(current);
         Vector rhs(cn_right->Height());
         cn_right->Mult(current, rhs);
         Vector next(current);
         cn_solver.Mult(rhs, next);
         ParGridFunction raw(&space);
         raw.SetFromTrueDofs(next);
         ParGridFunction stage1(raw);
         repaired_negative_averages.push_back(RepairCellAverages(space, stage1));
         ParGridFunction corrected(&space);
         const ProjectionCounts projection =
            ProjectField(local_projector, space, stage1, corrected);
         qp_cells.push_back(projection.qp);
         zero_average_cells.push_back(projection.zero_average);
         uncertified_cells.push_back(global_cells - projection.certified);
         const double correction = FieldL1Difference(raw, corrected);
         const double incoming_mass = FieldMass(raw);
         const double corrected_mass = FieldMass(corrected);
         relative_corrections.push_back(correction / std::max(std::abs(incoming_mass),
                                                              std::numeric_limits<double>::min()));
         masses.push_back(corrected_mass);
         state = corrected;
         if (rank == 0 && ((step + 1) % 32 == 0 || step + 1 == steps))
         {
            const double elapsed = std::chrono::duration<double>(
               std::chrono::steady_clock::now() - started).count();
            std::cout << "mature MFEM step " << step + 1 << "/" << steps
                      << ", elapsed=" << elapsed << "s" << std::endl;
         }
      }
      const double runtime = std::chrono::duration<double>(
         std::chrono::steady_clock::now() - started).count();
      if (adaptive_mode)
      {
         ExportAlignedCommonAverages(state,
            output_directory / "final_q2_subcell_averages.bin");
      }
      else
      {
         ExportSubcellAverages(state, nx, ny, nz,
            output_directory / "final_q2_subcell_averages.bin", 6);
      }
      struct rusage usage {};
      getrusage(RUSAGE_SELF, &usage);
      long local_peak_rss = usage.ru_maxrss, maximum_peak_rss = 0;
      MPI_Allreduce(&local_peak_rss, &maximum_peak_rss, 1, MPI_LONG, MPI_MAX,
                    MPI_COMM_WORLD);
      if (rank == 0)
      {
         const auto maximum_mass_error = *std::max_element(
            masses.begin(), masses.end(), [initial_mass](double a, double b)
            { return std::abs(a - initial_mass) < std::abs(b - initial_mass); });
         const double mean_correction = std::accumulate(
            relative_corrections.begin(), relative_corrections.end(), 0.0)
            / relative_corrections.size();
         std::ofstream summary(output_directory / "mature_summary.json");
         summary << std::setprecision(17)
                 << "{\n  \"mesh\": [" << nx << ", " << ny << ", " << nz << "],\n"
                 << "  \"amr\": " << (adaptive_mode ? "true" : "false") << ",\n"
                 << "  \"amr_levels\": " << (amr3_mode ? 3 : (amr2_mode ? 2 : (amr_mode ? 1 : 0))) << ",\n"
                 << "  \"cells\": " << global_cells << ",\n"
                 << "  \"initial_qp_cells\": " << initial_qp_cells << ",\n"
                 << "  \"initial_uncertified_cells\": " << initial_uncertified_cells << ",\n"
                 << "  \"initial_projection_l1_correction\": "
                 << initial_projection_correction << ",\n"
                 << "  \"steps\": " << steps << ",\n"
                 << "  \"initial_mass\": " << initial_mass << ",\n"
                 << "  \"final_mass\": " << masses.back() << ",\n"
                 << "  \"maximum_absolute_mass_error\": "
                 << std::abs(maximum_mass_error - initial_mass) << ",\n"
                 << "  \"mean_relative_l1_correction\": " << mean_correction << ",\n"
                 << "  \"maximum_relative_l1_correction\": "
                 << *std::max_element(relative_corrections.begin(), relative_corrections.end()) << ",\n"
                 << "  \"maximum_qp_cells\": "
                 << *std::max_element(qp_cells.begin(), qp_cells.end()) << ",\n"
                 << "  \"maximum_zero_average_cells\": "
                 << *std::max_element(zero_average_cells.begin(), zero_average_cells.end()) << ",\n"
                 << "  \"maximum_uncertified_cells\": "
                 << *std::max_element(uncertified_cells.begin(), uncertified_cells.end()) << ",\n"
                 << "  \"maximum_raw_negative_average_cells\": "
                 << *std::max_element(repaired_negative_averages.begin(), repaired_negative_averages.end()) << ",\n"
                 << "  \"optimizer_failures\": 0,\n"
                 << "  \"fallbacks\": 0,\n"
                 << "  \"whole_cell_positivity_certified\": "
                 << (std::all_of(uncertified_cells.begin(), uncertified_cells.end(),
                                 [](int count) { return count == 0; }) ? "true" : "false")
                 << ",\n"
                 << "  \"runtime_seconds\": " << runtime << ",\n"
                 << "  \"maximum_rank_peak_rss_kib\": " << maximum_peak_rss << "\n}\n";
      }
      delete cn_left;
      delete cn_right;
      delete M;
      delete A;
      return 0;
   }

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
         ProjectField(local_projector, space, next_field, corrected_field).qp);

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
