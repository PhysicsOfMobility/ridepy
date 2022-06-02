#ifndef RIDEPY_CPP_TESTS_H
#define RIDEPY_CPP_TESTS_H

#include <string>

const std::string excCharDefault = "\033[0m";
const std::string excCharError = "\033[31m";
const std::string excCharInit  = "\033[32m";
const std::string excCharInfo  = "\033[33m";

void test_misc();

void test_simpleSquareGridSimulation();

#endif // RIDEPY_CPP_TESTS_H
