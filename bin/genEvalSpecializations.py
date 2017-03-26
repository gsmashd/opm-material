#! /usr/bin/python
#
# This script provides "hand loop-unrolled" specializations of the
# Evaluation class of dense automatic differentiation so that the
# compiler can more easily emit SIMD instructions. In an ideal world,
# C++ compilers should be smart enough to do this themselfs, but
# contemporary compilers don't seem to exhibit enough brains.
#
# Usage: In the opm-material top-level source directory, run
# `./bin/genEvalSpecializations.py [MAX_DERIVATIVES]`. The script then
# generates specializations for Evaluations with up to MAX_DERIVATIVES
# derivatives. The default for MAX_DERIVATIVES is 12. To run this
# script, you need a python 2 installation where the Jinja2 module is
# available.
#
import os
import sys
import jinja2

maxDerivs = 12
if len(sys.argv) == 2:
    maxDerivs = int(sys.argv[1])

fileNames = []

specializationTemplate = \
"""// -*- mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*-
// vi: set et ts=4 sw=4 sts=4:
/*
  This file is part of the Open Porous Media project (OPM).

  OPM is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 2 of the License, or
  (at your option) any later version.

  OPM is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with OPM.  If not, see <http://www.gnu.org/licenses/>.

  Consult the COPYING file in the top-level source directory of this
  module for the precise wording of the license and the list of
  copyright holders.
*/
/*!
 * \\file
 *
{% if numDerivs < 0 %}\
 * \\brief Representation of an evaluation of a function and its derivatives w.r.t. a set
 *        of variables in the localized OPM automatic differentiation (AD) framework.
{% else %}\
 * \\brief This file specializes the dense-AD Evaluation class for {{ numDerivs }} derivatives.
{% endif %}\
 *
 * \\attention THIS FILE GETS AUTOMATICALLY GENERATED BY THE "{{ scriptName }}"
 *            SCRIPT. DO NOT EDIT IT MANUALLY!
 */
{% if numDerivs < 0 %}\
#ifndef OPM_DENSEAD_EVALUATION_HPP
#define OPM_DENSEAD_EVALUATION_HPP
{% else %}\
#ifndef OPM_DENSEAD_EVALUATION{{numDerivs}}_HPP
#define OPM_DENSEAD_EVALUATION{{numDerivs}}_HPP
{% endif %}\

#include "Math.hpp"

#include <opm/common/Valgrind.hpp>

#include <dune/common/version.hh>

#include <array>
#include <cmath>
#include <cassert>
#include <cstring>
#include <iostream>
#include <algorithm>

namespace Opm {
namespace DenseAd {

{% if numDerivs < 0 %}\
/*!
 * \\brief Represents a function evaluation and its derivatives w.r.t. a fixed set of
 *        variables.
 */
template <class ValueT, int numDerivs>
class Evaluation
{% else %}\
template <class ValueT>
class Evaluation<ValueT, {{ numDerivs }}>
{% endif %}\
{
public:
    //! field type
    typedef ValueT ValueType;

    //! number of derivatives
{% if numDerivs < 0 %}\
    static constexpr int size = numDerivs;
{% else %}\
    static constexpr int size = {{ numDerivs }};
{% endif %}\

protected:
    //! length of internal data vector
    static constexpr int length_ = size + 1;

    //! position index for value
    static constexpr int valuepos_ = 0;
    //! start index for derivatives
    static constexpr int dstart_ = 1;
    //! end+1 index for derivatives
    static constexpr int dend_ = length_;

public:
    //! default constructor
    Evaluation() : data_()
    {}

    //! copy other function evaluation
    Evaluation(const Evaluation& other)
{% if numDerivs < 0 %}\
       : data_(other.data_)
    { }
{% else %}\
    {
{%   for i in range(0, numDerivs+1) %}\
        data_[{{i}}] = other.data_[{{i}}];
{%   endfor %}\
    }
{% endif %}\

    // create an evaluation which represents a constant function
    //
    // i.e., f(x) = c. this implies an evaluation with the given value and all
    // derivatives being zero.
    template <class RhsValueType>
    Evaluation(const RhsValueType& c)
    {
        setValue( c );
        clearDerivatives();
        Valgrind::CheckDefined( data_ );
    }

    // create an evaluation which represents a constant function
    //
    // i.e., f(x) = c. this implies an evaluation with the given value and all
    // derivatives being zero.
    template <class RhsValueType>
    Evaluation(const RhsValueType& c, int varPos)
    {
        // The variable position must be in represented by the given variable descriptor
        assert(0 <= varPos && varPos < size);

        setValue( c );
        clearDerivatives();

        data_[varPos + dstart_] = 1.0;
        Valgrind::CheckDefined(data_);
    }

    // set all derivatives to zero
    void clearDerivatives()
    {
{% if numDerivs < 0 %}\
        for (int i = dstart_; i < dend_; ++i) {
            data_[i] = 0.0;
        }
{% else %}\
{%   for i in range(1, numDerivs+1) %}\
        data_[{{i}}] = 0.0;
{%   endfor %}\
{% endif %}\
    }

    // create a function evaluation for a "naked" depending variable (i.e., f(x) = x)
    template <class RhsValueType>
    static Evaluation createVariable(const RhsValueType& value, int varPos)
    {
        // copy function value and set all derivatives to 0, except for the variable
        // which is represented by the value (which is set to 1.0)
        return Evaluation( value, varPos );
    }

    // "evaluate" a constant function (i.e. a function that does not depend on the set of
    // relevant variables, f(x) = c).
    template <class RhsValueType>
    static Evaluation createConstant(const RhsValueType& value)
    {
        return Evaluation( value );
    }

    // print the value and the derivatives of the function evaluation
    void print(std::ostream& os = std::cout) const
    {
        // print value
        os << "v: " << value() << " / d:";

        // print derivatives
        for (int varIdx = 0; varIdx < size; ++varIdx) {
            os << " " << derivative(varIdx);
        }
    }

    // copy all derivatives from other
    void copyDerivatives(const Evaluation& other)
    {
{% if numDerivs < 0 %}\
        for (int i = dstart_; i < dend_; ++i) {
            data_[i] = other.data_[i];
        }
{% else %}\
{%   for i in range(1, numDerivs+1) %}\
        data_[{{i}}] = other.data_[{{i}}];
{%   endfor %}\
{% endif %}\
    }


    // add value and derivatives from other to this values and derivatives
    Evaluation& operator+=(const Evaluation& other)
    {
{% if numDerivs < 0 %}\
        for (int i = 0; i < length_; ++i) {
            data_[i] += other.data_[i];
        }
{% else %}\
{%   for i in range(0, numDerivs+1) %}\
        data_[{{i}}] += other.data_[{{i}}];
{%   endfor %}\
{% endif %}\

        return *this;
    }

    // add value from other to this values
    template <class RhsValueType>
    Evaluation& operator+=(const RhsValueType& other)
    {
        // value is added, derivatives stay the same
        data_[valuepos_] += other;

        return *this;
    }

    // subtract other's value and derivatives from this values
    Evaluation& operator-=(const Evaluation& other)
    {
{% if numDerivs < 0 %}\
        for (int i = 0; i < length_; ++i) {
            data_[i] -= other.data_[i];
        }
{% else %}\
{%   for i in range(0, numDerivs+1) %}\
        data_[{{i}}] -= other.data_[{{i}}];
{%   endfor %}\
{% endif %}\

        return *this;
    }

    // subtract other's value from this values
    template <class RhsValueType>
    Evaluation& operator-=(const RhsValueType& other)
    {
        // for constants, values are subtracted, derivatives stay the same
        data_[ valuepos_ ] -= other;

        return *this;
    }

    // multiply values and apply chain rule to derivatives: (u*v)' = (v'u + u'v)
    Evaluation& operator*=(const Evaluation& other)
    {
        // while the values are multiplied, the derivatives follow the product rule,
        // i.e., (u*v)' = (v'u + u'v).
        const ValueType u = this->value();
        const ValueType v = other.value();

        // value
        data_[valuepos_] *= v ;

        //  derivatives
{% if numDerivs < 0 %}\
        for (int i = dstart_; i < dend_; ++i) {
            data_[i] = data_[i] * v + other.data_[i] * u;
        }
{% else %}\
{%   for i in range(1, numDerivs+1) %}\
        data_[{{i}}] = data_[{{i}}] * v + other.data_[{{i}}] * u;
{%   endfor %}\
{% endif %}\

        return *this;
    }

    // m(c*u)' = c*u'
    template <class RhsValueType>
    Evaluation& operator*=(const RhsValueType& other)
    {
{% if numDerivs < 0 %}\
        for (int i = 0; i < length_; ++i) {
            data_[i] *= other;
        }
{% else %}\
{%   for i in range(0, numDerivs+1) %}\
        data_[{{i}}] *= other;
{%   endfor %}\
{% endif %}\

        return *this;
    }

    // m(u*v)' = (v'u + u'v)
    Evaluation& operator/=(const Evaluation& other)
    {
        // values are divided, derivatives follow the rule for division, i.e., (u/v)' = (v'u - u'v)/v^2.
        const ValueType v_vv = 1.0 / other.value();
        const ValueType u_vv = value() * v_vv * v_vv;

        // value
        data_[valuepos_] *= v_vv;

        //  derivatives
{% if numDerivs < 0 %}\
        for (int i = dstart_; i < dend_; ++i) {
            data_[i] = data_[i] * v_vv - other.data_[i] * u_vv;
        }
{% else %}\
{%   for i in range(1, numDerivs+1) %}\
        data_[{{i}}] = data_[{{i}}] * v_vv - other.data_[{{i}}] * u_vv;
{%   endfor %}\
{% endif %}\

        return *this;
    }

    // divide value and derivatives by value of other
    template <class RhsValueType>
    Evaluation& operator/=(const RhsValueType& other)
    {
        const ValueType tmp = 1.0/other;

{% if numDerivs < 0 %}\
        for (int i = 0; i < length_; ++i) {
            data_[i] *= tmp;
        }
{% else %}\
{%   for i in range(0, numDerivs+1) %}\
        data_[{{i}}] *= tmp;
{%   endfor %}\
{% endif %}\

        return *this;
    }

    // division of a constant by an Evaluation
    template <class RhsValueType>
    static inline Evaluation divide(const RhsValueType& a, const Evaluation& b)
    {
        Evaluation result;

        const ValueType tmp = 1.0/b.value();
        result.setValue( a*tmp );
        const ValueType df_dg = - result.value()*tmp;

{% if numDerivs < 0 %}\
        for (int i = dstart_; i < dend_; ++i) {
            result.data_[i] = df_dg * b.data_[i];
        }
{% else %}\
{%   for i in range(1, numDerivs+1) %}\
        result.data_[{{i}}] = df_dg * b.data_[{{i}}];
{%   endfor %}\
{% endif %}\

        return result;
    }

    // add two evaluation objects
    Evaluation operator+(const Evaluation& other) const
    {
        Evaluation result(*this);

        result += other;

        return result;
    }

    // add constant to this object
    template <class RhsValueType>
    Evaluation operator+(const RhsValueType& other) const
    {
        Evaluation result(*this);

        result += other;

        return result;
    }

    // subtract two evaluation objects
    Evaluation operator-(const Evaluation& other) const
    {
        Evaluation result(*this);

        result -= other;

        return result;
    }

    // subtract constant from evaluation object
    template <class RhsValueType>
    Evaluation operator-(const RhsValueType& other) const
    {
        Evaluation result(*this);

        result -= other;

        return result;
    }

    // negation (unary minus) operator
    Evaluation operator-() const
    {
        Evaluation result;

        // set value and derivatives to negative
{% if numDerivs < 0 %}\
        for (int i = 0; i < length_; ++i) {
            result.data_[i] = - data_[i];
        }
{% else %}\
{%   for i in range(0, numDerivs+1) %}\
        result.data_[{{i}}] = - data_[{{i}}];
{%   endfor %}\
{% endif %}\

        return result;
    }

    Evaluation operator*(const Evaluation& other) const
    {
        Evaluation result(*this);

        result *= other;

        return result;
    }

    template <class RhsValueType>
    Evaluation operator*(const RhsValueType& other) const
    {
        Evaluation result(*this);

        result *= other;

        return result;
    }

    Evaluation operator/(const Evaluation& other) const
    {
        Evaluation result(*this);

        result /= other;

        return result;
    }

    template <class RhsValueType>
    Evaluation operator/(const RhsValueType& other) const
    {
        Evaluation result(*this);

        result /= other;

        return result;
    }

    template <class RhsValueType>
    Evaluation& operator=(const RhsValueType& other)
    {
        setValue( other );
        clearDerivatives();

        return *this;
    }

    // copy assignment from evaluation
    Evaluation& operator=(const Evaluation& other)
    {
{% if numDerivs < 0 %}\
        for (int i = 0; i < length_; ++i) {
            data_[i] = other.data_[i];
        }
{% else %}\
{%   for i in range(0, numDerivs+1) %}\
        data_[{{i}}] = other.data_[{{i}}];
{%   endfor %}\
{% endif %}\

        return *this;
    }

    template <class RhsValueType>
    bool operator==(const RhsValueType& other) const
    { return value() == other; }

    bool operator==(const Evaluation& other) const
    {
        for (int idx = 0; idx < length_; ++idx) {
            if (data_[idx] != other.data_[idx]) {
                return false;
            }
        }
        return true;
    }

    bool operator!=(const Evaluation& other) const
    { return !operator==(other); }

    template <class RhsValueType>
    bool operator>(RhsValueType other) const
    { return value() > other; }

    bool operator>(const Evaluation& other) const
    { return value() > other.value(); }

    template <class RhsValueType>
    bool operator<(RhsValueType other) const
    { return value() < other; }

    bool operator<(const Evaluation& other) const
    { return value() < other.value(); }

    template <class RhsValueType>
    bool operator>=(RhsValueType other) const
    { return value() >= other; }

    bool operator>=(const Evaluation& other) const
    { return value() >= other.value(); }

    template <class RhsValueType>
    bool operator<=(RhsValueType other) const
    { return value() <= other; }

    bool operator<=(const Evaluation& other) const
    { return value() <= other.value(); }

    // return value of variable
    const ValueType& value() const
    { return data_[valuepos_]; }

    // set value of variable
    template <class RhsValueType>
    void setValue(const RhsValueType& val)
    { data_[valuepos_] = val; }

    // return varIdx'th derivative
    const ValueType& derivative(int varIdx) const
    {
        assert(0 <= varIdx && varIdx < size);

        return data_[dstart_ + varIdx];
    }

    // set derivative at position varIdx
    void setDerivative(int varIdx, const ValueType& derVal)
    {
        assert(0 <= varIdx && varIdx < size);

        data_[dstart_ + varIdx] = derVal;
    }

private:
    std::array<ValueT, length_> data_;
};

{% if numDerivs < 0 %}\
// the generic operators are only required for the unspecialized case
template <class RhsValueType, class ValueType, int numVars>
bool operator<(const RhsValueType& a, const Evaluation<ValueType, numVars>& b)
{ return b > a; }

template <class RhsValueType, class ValueType, int numVars>
bool operator>(const RhsValueType& a, const Evaluation<ValueType, numVars>& b)
{ return b < a; }

template <class RhsValueType, class ValueType, int numVars>
bool operator<=(const RhsValueType& a, const Evaluation<ValueType, numVars>& b)
{ return b >= a; }

template <class RhsValueType, class ValueType, int numVars>
bool operator>=(const RhsValueType& a, const Evaluation<ValueType, numVars>& b)
{ return b <= a; }

template <class RhsValueType, class ValueType, int numVars>
bool operator!=(const RhsValueType& a, const Evaluation<ValueType, numVars>& b)
{ return a != b.value(); }

template <class RhsValueType, class ValueType, int numVars>
Evaluation<ValueType, numVars> operator+(const RhsValueType& a, const Evaluation<ValueType, numVars>& b)
{
    Evaluation<ValueType, numVars> result(b);
    result += a;
    return result;
}

template <class RhsValueType, class ValueType, int numVars>
Evaluation<ValueType, numVars> operator-(const RhsValueType& a, const Evaluation<ValueType, numVars>& b)
{
    Evaluation<ValueType, numVars> result(a);
    result -= b;
    return result;
}

template <class RhsValueType, class ValueType, int numVars>
Evaluation<ValueType, numVars> operator/(const RhsValueType& a, const Evaluation<ValueType, numVars>& b)
{
    return Evaluation<ValueType, numVars>::divide(a, b);
}

template <class RhsValueType, class ValueType, int numVars>
Evaluation<ValueType, numVars> operator*(const RhsValueType& a, const Evaluation<ValueType, numVars>& b)
{
    Evaluation<ValueType, numVars> result(b);
    result *= a;
    return result;
}

template <class ValueType, int numVars>
std::ostream& operator<<(std::ostream& os, const Evaluation<ValueType, numVars>& eval)
{
    os << eval.value();
    return os;
}
{% endif %}\
} } // namespace DenseAd, Opm

{% if numDerivs < 0 %}\
// In Dune 2.3, the Evaluation.hpp header must be included before the fmatrix.hh
// header. Dune 2.4+ does not suffer from this because of some c++-foo.
//
// for those who are wondering: in C++ function templates cannot be partially
// specialized, and function argument overloads must be known _before_ they are used. The
// latter is what we do for the 'Dune::fvmeta::absreal()' function.
//
// consider the following test program:
//
// double foo(double i)
// { return i; }
//
// void bar()
// { std::cout << foo(0) << "\\n"; }
//
// int foo(int i)
// { return i + 1; }
//
// void foobar()
// { std::cout << foo(0) << "\\n"; }
//
// this will print '0' for bar() and '1' for foobar()...
#if !(DUNE_VERSION_NEWER(DUNE_COMMON, 2,4))

namespace Opm {
namespace DenseAd {
template <class ValueType, int numVars>
Evaluation<ValueType, numVars> abs(const Evaluation<ValueType, numVars>&);
}}

namespace std {
template <class ValueType, int numVars>
const Opm::DenseAd::Evaluation<ValueType, numVars> abs(const Opm::DenseAd::Evaluation<ValueType, numVars>& x)
{ return Opm::DenseAd::abs(x); }

} // namespace std

#if defined DUNE_DENSEMATRIX_HH
#warning \\
 "Due to some C++ peculiarity regarding function overloads, the 'Evaluation.hpp'" \\
 "header file must be included before Dune's 'densematrix.hh' for Dune < 2.4. " \\
 "(If Evaluations are to be used in conjunction with a dense matrix.)"
#endif

#endif

// this makes the Dune matrix/vector classes happy...
#include <dune/common/ftraits.hh>

namespace Dune {
template <class ValueType, int numVars>
struct FieldTraits<Opm::DenseAd::Evaluation<ValueType, numVars> >
{
public:
    typedef Opm::DenseAd::Evaluation<ValueType, numVars> field_type;
    // setting real_type to field_type here potentially leads to slightly worse
    // performance, but at least it makes things compile.
    typedef field_type real_type;
};

} // namespace Dune

#include "EvaluationSpecializations.hpp"

#endif // OPM_DENSEAD_EVALUATION_HPP
{% else %}\
#endif // OPM_DENSEAD_EVALUATION{{numDerivs}}_HPP
{% endif %}\
"""

includeSpecializationsTemplate = \
"""// -*- mode: C++; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4 -*-
// vi: set et ts=4 sw=4 sts=4:
/*
  This file is part of the Open Porous Media project (OPM).

  OPM is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 2 of the License, or
  (at your option) any later version.

  OPM is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with OPM.  If not, see <http://www.gnu.org/licenses/>.

  Consult the COPYING file in the top-level source directory of this
  module for the precise wording of the license and the list of
  copyright holders.
*/
/*!
 * \\file
 *
 * \\brief This file includes all specializations for the dense-AD Evaluation class.
 *
 * \\attention THIS FILE GETS AUTOMATICALLY GENERATED BY THE "{{ scriptName }}"
 *            SCRIPT. DO NOT EDIT IT MANUALLY!
 */
#ifndef OPM_DENSEAD_EVALUATION_SPECIALIZATIONS_HPP
#define OPM_DENSEAD_EVALUATION_SPECIALIZATIONS_HPP

{% for fileName in fileNames %}\
#include <{{ fileName }}>
{% endfor %}\

#endif // OPM_DENSEAD_EVALUATION_SPECIALIZATIONS_HPP
"""

print ("Generating generic template class")
fileName = "opm/material/densead/Evaluation.hpp"
template = jinja2.Template(specializationTemplate)
fileContents = template.render(numDerivs=-1, scriptName=os.path.basename(sys.argv[0]))

f = open(fileName, "w")
f.write(fileContents)
f.close()

for numDerivs in range(1, maxDerivs + 1):
    print ("Generating specialization for %d derivatives"%numDerivs)

    fileName = "opm/material/densead/Evaluation%d.hpp"%numDerivs
    fileNames.append(fileName)

    template = jinja2.Template(specializationTemplate)
    fileContents = template.render(numDerivs=numDerivs, scriptName=os.path.basename(sys.argv[0]))

    f = open(fileName, "w")
    f.write(fileContents)
    f.close()

template = jinja2.Template(includeSpecializationsTemplate)
fileContents = template.render(fileNames=fileNames, scriptName=os.path.basename(sys.argv[0]))

f = open("opm/material/densead/EvaluationSpecializations.hpp", "w")
f.write(fileContents)
f.close()
