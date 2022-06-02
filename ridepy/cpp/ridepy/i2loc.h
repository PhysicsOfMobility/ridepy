#ifndef I2LOC_H
#define I2LOC_H

#include <ostream>
#include <utility>

namespace ridepy {

/*!
 * \brief A 2-dimensional vector of integer numbers used to store locations on a square grid
 */
typedef std::pair<int, int> I2loc;

inline bool operator==(const I2loc &v1, const I2loc &v2){
    return v1.first == v2.first && v1.second == v2.second;
}

/*!
 * \brief Computes the direct sum of \p v1 and \p v2
 */
inline I2loc operator+ (const I2loc &v1, const I2loc &v2){
    return {v1.first+v2.first, v1.second+v2.second};
}

/*!
 * \brief Computes the componentwise difference of \p v1 and \p v2
 */
inline I2loc operator- (const I2loc &v1, const I2loc &v2){
    return {v1.first-v2.first, v1.second-v2.second};
}

/*!
 * \brief Mupliplies \p v with a scalar \p a
 */
inline I2loc operator* (const I2loc &v, const double a){
    return {v.first*a,v.second*a};
}

/*!
 * \brief Mupliplies \p v with a scalar \p a
 */
inline I2loc operator* (const double a, const I2loc &v){
    return {v.first*a,v.second*a};
}

/*!
 * \brief Divides a \p v by a scalar \p a
 */
inline I2loc operator/ (const I2loc &v, const double a){
    return {v.first/a,v.second/a};
}

/*!
 * \brief Returns the length of the vector
 */
inline double abs(const I2loc &v){
    return std::abs(v.first) + std::abs(v.second);
}

/*!
 * \brief Defines how to stringify a \a I2loc when sending it to an ostream like \a cout
 *
 * This outputs the \a I2loc in the form "(first,second)".
 */
inline std::ostream &operator<<(std::ostream &os, const I2loc &v){
    os << "(" << v.first << "," << v.second << ")";
    return os;
}

} // namespace ridepy

#endif // I2LOC_H
