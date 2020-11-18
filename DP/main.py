import csv
import itertools
import timeit
import numpy


# zwraca macierz i jej rozmiar na podstawie danego pliku
def getDataFromFile(filename):
    file = open(filename, 'r')
    size = file.readline()
    matrix = numpy.array(parseStringstoIntegers(file.readline().split()))

    for line in file.readlines():
        line = line.split()
        if len(line) > 1:
            tmp = parseStringstoIntegers(line)
            matrix = numpy.vstack([matrix, tmp])
    return [matrix, size]


# parsuje linie z pliku do wiersza macierzy
def parseStringstoIntegers(line):
    array = [int(n) for n in line if n != '']
    return numpy.array(array)


# zwraca koszt i najtańszą ścieżkę
# @profile
def solve(matrix, size):
    '''
        base - słownik w postaci  base[vertices, last] : (cost, parent)
        vertices - zbiór wierzchołków na danej ścieżce
        last - ostatni wierzchołek na ścieżce
        cost - suma wszystki kosztów przejścia ścieżką
        parent - indeks przedostatniego wierzchołka
    '''
    base = {}

    # wypełnienie słownika przypadkami jednoelementowymi
    for i in range(1, size):
        base[(1 << i, i)] = (matrix[0][i], 0)

    # stopniowe wypełnianie słownika ścieżkami o co raz większej długości
    for subset_size in range(2, size):
        for subset in itertools.combinations(range(1, size), subset_size):

            bits = 0
            for bit in subset:
                bits = bits | (1 << bit)

            # znajduje najniższy koszt dla tego podzbioru
            for i in subset:
                prev = bits & ~(1 << i)

                cost = []
                for m in subset:
                    if m == 0 or m == i:
                        continue
                    cost.append((base[(prev, m)][0] + matrix[m][i], m))
                base[(bits, i)] = min(cost)

    bits = (2 ** size - 1) - 1
    cost = []

    for i in range(1, size):
        cost.append((base[(bits, i)][0] + matrix[i][0], i))

    final_cost, parent = min(cost)

    path = [0]

    # Odtworzenie trasy
    for i in range(size - 1):
        path.append(parent)  # dodaj wierzchołek do ścieżki
        next_bits = bits & ~(1 << parent)  # ustawienie mniejszego poziomu
        tmp, parent = base[(bits, parent)]
        bits = next_bits

    path.append(0)

    return final_cost, list(reversed(path))


def getConfig():
    file = open("config.ini", "r")
    config = []
    for line in file.readlines():
        if line.find('.csv') > 1:
            global outputFile
            outputFile = line
            break

        tmp = line.split()
        config.append({'file': tmp[0], 'repetitions': tmp[1], 'cost': tmp[2], 'path': tmp[3]})

    return config


def group():
    config = getConfig()

    new = {}
    with open(outputFile, 'w', newline='') as csvfile:
        fieldnames = ['file', 'repetitions', 'cost', 'path', 'time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_NONE)
        writer.writeheader()

        for item in config:
            data = getDataFromFile(item['file'])
            matrix = data[0]
            size = int(data[1])
            repetitions = int(item['repetitions'])

            if repetitions:
                writer.writerow({'file': item['file'], 'repetitions': repetitions})

                for tmp in range(repetitions):
                    begin = timeit.default_timer()
                    results = solve(matrix, size)
                    end = timeit.default_timer()
                    print(results)
                    writer.writerow(
                        {'cost': results[0], 'path': str(results[1]).strip(",0"), 'time': round((end - begin), 5)})

                    new[item['file']] = {'file': item['file'], 'repetitions': repetitions, 'cost': results[0],
                                         'path': str(results[1]).strip(",0"), 'time': round((end - begin), 5)}

    return new


# def one():
#     data = getDataFromFile("testData/tsp_12.txt")
#     matrix = data[0]
#     size = int(data[1])
#
#     begin = timeit.default_timer()
#     results = solve(matrix, size)
#     end = timeit.default_timer()
#
#     print(results)
#     print(end - begin)


def main():
    output = group()
    print(output)


main()
