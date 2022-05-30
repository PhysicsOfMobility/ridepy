#ifndef RidePy_CPP_R2LOC_H
#define RidePy_CPP_R2LOC_H

#include <cmath>
#include <ostream>
#include <utility>

namespace ridepy {

/*!
 * \brief A 2-dimensional vector of floating point numbers used to store locations in the 2D plane
 */
typedef std::pair<double, double> R2loc;

/*!
 * \brief Computes the direct sum of \p v1 and \p v2
 */
inline R2loc operator+ (const R2loc &v1, const R2loc &v2){
    return {v1.first+v2.first, v1.second+v2.second};
}

/*!
 * \brief Computes the componentwise difference of \p v1 and \p v2
 */
inline R2loc operator- (const R2loc &v1, const R2loc &v2){
    return {v1.first-v2.first, v1.second-v2.second};
}

/*!
 * \brief Mupliplies \p v with a scalar \p a
 */
inline R2loc operator* (const R2loc &v, const double a){
    return {v.first*a,v.second*a};
}

/*!
 * \brief Mupliplies \p v with a scalar \p a
 */
inline R2loc operator* (const double a, const R2loc &v){
    return {v.first*a,v.second*a};
}

/*!
 * \brief Divides a \p v by a scalar \p a
 */
inline R2loc operator/ (const R2loc &v, const double a){
    return {v.first/a,v.second/a};
}

/*!
 * \brief Returns the length of the vector
 */
inline double abs(const R2loc &v){
    return sqrt(v.first*v.first + v.second*v.second);
}

/*!
 * \brief Returns the square of the vector length. Is faster than abs()
 */
inline double abs2(const R2loc &v){
    return v.first*v.first + v.second*v.second;
}

/*!
 * \brief Defines how to stringify a \a R2loc when sending it to an ostream like \a cout
 *
 * This outputs the \a R2loc in the form "(first,second)".
 */
inline std::ostream &operator<<(std::ostream &os, const R2loc &v){
    os << "(" << v.first << "," << v.second << ")";
    return os;
}

} // namespace ridepy

#endif // RidePy_CPP_R2LOC_H
