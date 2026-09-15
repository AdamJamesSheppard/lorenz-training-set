#include "mfem.hpp"

#include <cmath>
#include <iomanip>
#include <iostream>

using namespace mfem;

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

class SmoothDensity final : public Coefficient
{
public:
   double Eval(ElementTransformation &transformation,
               const IntegrationPoint &point) override
   {
      Vector x(3);
      transformation.Transform(point, x);
      const double q = x[0] * x[0] / 36.0 + x[1] * x[1] / 49.0
                       + (x[2] - 24.0) * (x[2] - 24.0) / 25.0;
      return std::exp(-0.5 * q);
   }
};

int main(int argc, char *argv[])
{
   Mpi::Init(argc, argv);
   const int rank = Mpi::WorldRank();
   int nx = 4, ny = 5, nz = 5;
   if (argc == 4)
   {
      nx = std::stoi(argv[1]);
      ny = std::stoi(argv[2]);
      nz = std::stoi(argv[3]);
   }
   MFEM_VERIFY(nx > 0 && ny > 0 && nz > 0, "positive mesh sizes required");

   Mesh serial = Mesh::MakeCartesian3D(
      nx, ny, nz, Element::HEXAHEDRON, 1, 60.0, 80.0, 80.0);
   for (int vertex = 0; vertex < serial.GetNV(); ++vertex)
   {
      double *x = serial.GetVertex(vertex);
      x[0] -= 30.0;
      x[1] -= 40.0;
      x[2] -= 10.0;
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
   MatrixConstantCoefficient diffusion(tensor);
   LorenzDrift drift;

   ParBilinearForm mass(&space);
   mass.AddDomainIntegrator(new MassIntegrator(one));
   mass.Assemble();
   mass.Finalize();
   HypreParMatrix *M = mass.ParallelAssemble();

   constexpr double sigma = -1.0;
   constexpr double kappa = 36.0;
   ParBilinearForm spatial(&space);
   spatial.AddDomainIntegrator(
      new ConservativeConvectionIntegrator(drift, -1.0));
   spatial.AddInteriorFaceIntegrator(
      new DGTraceIntegrator(drift, -1.0, -0.5));
   spatial.AddDomainIntegrator(new DiffusionIntegrator(diffusion));
   spatial.AddInteriorFaceIntegrator(
      new DGDiffusionIntegrator(diffusion, sigma, kappa));
   spatial.Assemble();
   spatial.Finalize();
   HypreParMatrix *A = spatial.ParallelAssemble();

   ParGridFunction constant(&space);
   constant.ProjectCoefficient(one);
   Vector constant_true;
   constant.GetTrueDofs(constant_true);

   SmoothDensity smooth_density;
   ParGridFunction initial(&space);
   initial.ProjectCoefficient(smooth_density);
   Vector initial_true;
   initial.GetTrueDofs(initial_true);

   constexpr double dt = 0.00015625;
   HypreParMatrix *cn_left = Add(1.0, *M, 0.5 * dt, *A);
   HypreParMatrix *cn_right = Add(1.0, *M, -0.5 * dt, *A);
   Vector right_hand_side(cn_right->Height());
   cn_right->Mult(initial_true, right_hand_side);
   Vector next(initial_true);
   HypreILU preconditioner;
   preconditioner.SetType(0);
   preconditioner.SetLevelOfFill(1);
   preconditioner.SetMaxIter(1);
   preconditioner.SetTol(0.0);
   preconditioner.SetPrintLevel(0);
   preconditioner.SetOperator(*cn_left);
   HypreGMRES solver(*cn_left);
   solver.SetTol(1.0e-12);
   solver.SetAbsTol(1.0e-15);
   solver.SetMaxIter(1000);
   solver.SetKDim(100);
   solver.SetPrintLevel(0);
   solver.SetPreconditioner(preconditioner);
   solver.iterative_mode = false;
   solver.Mult(right_hand_side, next);
   int cn_iterations = 0;
   double cn_reported_residual = 0.0;
   solver.GetNumIterations(cn_iterations);
   solver.GetFinalResidualNorm(cn_reported_residual);
   Vector cn_residual(right_hand_side);
   cn_left->AddMult(next, cn_residual, -1.0);
   const double local_cn_norms[2] = {
      cn_residual * cn_residual, right_hand_side * right_hand_side
   };
   double global_cn_norms[2] = {0.0, 0.0};
   MPI_Allreduce(local_cn_norms, global_cn_norms, 2, MPI_DOUBLE, MPI_SUM,
                 MPI_COMM_WORLD);
   const double cn_true_relative_residual =
      std::sqrt(global_cn_norms[0] / global_cn_norms[1]);

   Vector mass_initial(M->Height()), mass_next(M->Height());
   M->Mult(initial_true, mass_initial);
   M->Mult(next, mass_next);
   double local_masses[2] = {
      constant_true * mass_initial, constant_true * mass_next
   };
   double global_masses[2] = {0.0, 0.0};
   MPI_Allreduce(local_masses, global_masses, 2, MPI_DOUBLE, MPI_SUM,
                 MPI_COMM_WORLD);

   double maximum_absolute_conservation = 0.0;
   double maximum_normalized_conservation = 0.0;
   constexpr int number_of_trials = 5;
   for (int trial_index = 0; trial_index < number_of_trials; ++trial_index)
   {
      Vector trial(A->Width());
      for (int i = 0; i < trial.Size(); ++i)
      {
         const double phase = i + 1 + 31 * rank;
         trial[i] = std::sin((0.11 + 0.03 * trial_index) * phase)
                    + 0.25 * std::cos((0.07 + 0.01 * trial_index) * phase);
      }
      Vector residual(A->Height());
      A->Mult(trial, residual);
      const double local_values[3] = {
         constant_true * residual,
         constant_true * constant_true,
         residual * residual
      };
      double global_values[3] = {0.0, 0.0, 0.0};
      MPI_Allreduce(local_values, global_values, 3, MPI_DOUBLE, MPI_SUM,
                    MPI_COMM_WORLD);
      const double absolute = std::abs(global_values[0]);
      const double scale = std::sqrt(global_values[1] * global_values[2]);
      const double normalized = scale > 0.0 ? absolute / scale : absolute;
      maximum_absolute_conservation =
         std::max(maximum_absolute_conservation, absolute);
      maximum_normalized_conservation =
         std::max(maximum_normalized_conservation, normalized);
   }

   if (rank == 0)
   {
      std::cout << std::setprecision(17)
                << "MFEM_UNIFORM_EQUIVALENCE_PROBE\n"
                << "cells=" << nx << "x" << ny << "x" << nz << "\n"
                << "global_q2_dofs=" << space.GlobalTrueVSize() << "\n"
                << "mass_rows=" << M->GetGlobalNumRows() << "\n"
                << "spatial_rows=" << A->GetGlobalNumRows() << "\n"
                << "number_of_operator_action_trials=" << number_of_trials << "\n"
                << "maximum_absolute_mass_functional_residual="
                << maximum_absolute_conservation << "\n"
                << "maximum_normalized_mass_functional_residual="
                << maximum_normalized_conservation << "\n"
                << "cn_dt=" << dt << "\n"
                << "cn_iterations=" << cn_iterations << "\n"
                << "cn_reported_residual=" << cn_reported_residual << "\n"
                << "cn_true_relative_residual=" << cn_true_relative_residual << "\n"
                << "cn_initial_mass=" << global_masses[0] << "\n"
                << "cn_next_mass=" << global_masses[1] << "\n"
                << "cn_absolute_mass_change="
                << std::abs(global_masses[1] - global_masses[0]) << "\n"
                << "full_spd_tensor=true\n"
                << "interior_upwind_faces=true\n"
                << "interior_sipg_faces=true\n"
                << "boundary_total_flux=omitted_zero\n";
   }

   delete cn_right;
   delete cn_left;
   delete A;
   delete M;
   const bool passed = maximum_normalized_conservation <= 1.0e-13
                       && cn_true_relative_residual <= 1.0e-11
                       && std::abs(global_masses[1] - global_masses[0]) <= 1.0e-9;
   return passed ? 0 : 2;
}
