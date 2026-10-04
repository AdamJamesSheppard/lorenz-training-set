#pragma once
#include "mfem.hpp"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <vector>

// Positive trilinear density from a binned Lorenz trajectory, on the frozen
// 45x54x54 background grid. No Gaussian mixture or covariance fit is used.
class EmpiricalPrior final : public mfem::Coefficient
{
   std::vector<double> values;
public:
   explicit EmpiricalPrior(const char *path) : values(46*55*55)
   {
      std::ifstream input(path,std::ios::binary);
      input.read(reinterpret_cast<char *>(values.data()),values.size()*sizeof(double));
      MFEM_VERIFY(input.good(),"could not read empirical vertex density");
      for (double v:values) { MFEM_VERIFY(std::isfinite(v)&&v>=0,"invalid empirical density"); }
   }
   double Eval(mfem::ElementTransformation &T,const mfem::IntegrationPoint &ip) override
   {
      mfem::Vector x(3); T.Transform(ip,x);
      const int counts[3]={45,54,54};
      const double low[3]={-30,-40,-10},high[3]={30,40,70};
      int index[3]; double fraction[3];
      for(int a=0;a<3;++a)
      {
         const double v=std::clamp((x[a]-low[a])*counts[a]/(high[a]-low[a]),0.,double(counts[a]));
         index[a]=std::min(counts[a]-1,int(std::floor(v))); fraction[a]=v-index[a];
      }
      double result=0.;
      for(int i=0;i<2;++i) for(int j=0;j<2;++j) for(int k=0;k<2;++k)
      {
         const double w=(i?fraction[0]:1-fraction[0])*(j?fraction[1]:1-fraction[1])*(k?fraction[2]:1-fraction[2]);
         result+=w*values[((index[0]+i)*55+index[1]+j)*55+index[2]+k];
      }
      return result;
   }
};
