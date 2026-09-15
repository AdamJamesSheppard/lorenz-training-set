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
   Vector trial(A->Width());
   for (int i = 0; i < trial.Size(); ++i)
   {
      trial[i] = std::sin(0.17 * (i + 1 + 31 * rank));
   }
   Vector residual(A->Height());
   A->Mult(trial, residual);
   const double local_conservation = constant_true * residual;
   double conservation = 0.0;
   MPI_Allreduce(&local_conservation, &conservation, 1, MPI_DOUBLE, MPI_SUM,
                 MPI_COMM_WORLD);

   if (rank == 0)
   {
      std::cout << std::setprecision(17)
                << "MFEM_UNIFORM_EQUIVALENCE_PROBE\n"
                << "cells=" << nx << "x" << ny << "x" << nz << "\n"
                << "global_q2_dofs=" << space.GlobalTrueVSize() << "\n"
                << "mass_rows=" << M->GetGlobalNumRows() << "\n"
                << "spatial_rows=" << A->GetGlobalNumRows() << "\n"
                << "constant_test_conservation_residual=" << conservation << "\n"
                << "full_spd_tensor=true\n"
                << "interior_upwind_faces=true\n"
                << "interior_sipg_faces=true\n"
                << "boundary_total_flux=omitted_zero\n";
   }

   delete A;
   delete M;
   return std::abs(conservation) <= 1.0e-9 ? 0 : 2;
}
