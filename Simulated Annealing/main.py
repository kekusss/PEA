import csv
import math
import random
import timeit
import numpy


# zwraca macierz i jej rozmiar na podstawie pliku z macierza
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


# zwraca macierz i jej rozmiar na podstawie pliku ze wspolrzednymi
def getDataAndConvert(filename):
    file = open(filename, 'r')
    size = file.readline()
    a = []
    b = []

    for line in file.readlines():
        line = line.split()
        if len(line) > 1:
            tmp = parseStringstoIntegers(line)
            a.append(tmp[1])
            b.append(tmp[2])

    coords = numpy.column_stack((a, b))

    matrix = numpy.sqrt((numpy.square(coords[:, numpy.newaxis] - coords).sum(axis=2)))

    return [matrix, size]


# parsuje linie z pliku do wiersza macierzy
def parseStringstoIntegers(line):
    array = [float(n) for n in line if n != '']
    return numpy.array(array)


# wylicza koszt
def cost(sol, matrix):
    return sum([matrix[i, j] for i, j in zip(sol, sol[1:] + [sol[0]])])


def acceptance_probability(candidate_cost, temp):
    return math.exp(-abs(candidate_cost - current_cost) / temp)


'''
 akceptacja z prawdopodobienstwem rownym 1, jeśli nowe rozwiazanie jest lepsze od obecnego,
w przeciwnym wypadku akceptuje z prawdopodobienstwem rownym wyliczonemy w acceptance_probability, Algorytm Metropolisa
'''
def accept(candidate, temp, matrix):
    global current_solution, best_solution, min_cost, current_cost

    candidate_cost = cost(candidate, matrix)
    if candidate_cost < current_cost:
        current_cost = candidate_cost
        current_solution = candidate

        if candidate_cost < min_cost:
            min_cost = candidate_cost
            best_solution = candidate

    else:
        # przyjmij rozwiazanie z danym prawdopodobienstwem
        if random.random() < acceptance_probability(candidate_cost, temp):
            current_cost = candidate_cost
            current_solution = candidate


def get_neighbour(neighbourhood_type, candidate, size):
    if neighbourhood_type == "2opt":
        l = random.randint(2, size - 1)
        i = random.randint(1, size - l)
        candidate[i: (i + l)] = reversed(candidate[i: (i + l)])  # wymień losowy fragment listy kandydatów
    else:
        l = random.randint(0, size - 1)
        i = random.randint(0, size - 1)

        if i > l:
            candidate.insert(i, candidate[l])
            candidate.remove(candidate[l])
        elif i < l:
            candidate.insert(i, candidate[l])
            candidate.remove(candidate[l+1])

    return candidate

# zwraca koszt i najtańszą ścieżkę
# @profile
def solve(matrix, temp, stopping_temp, stopping_iter, cooling_type, neighbourhood_type):
    global current_solution, best_solution, min_cost, current_cost
    size = len(matrix)
    iteration = 1

    current_solution = getFirstSolution(matrix)
    best_solution = current_solution
    solution_history = [current_solution]

    current_cost = cost(current_solution, matrix)
    initial_cost = current_cost
    min_cost = current_cost
    cost_list = [current_cost]

    print('Intial cost: ', current_cost)

    # wyżarzanie
    while temp >= stopping_temp and iteration < stopping_iter:
        candidate = list(current_solution)

        candidate = get_neighbour(neighbourhood_type, candidate, size)

        accept(candidate, temp, matrix)

        temp = cool(temp, cooling_type)
        iteration += 1
        cost_list.append(current_cost)
        solution_history.append(current_solution)

    print('Minimum cost: ', min_cost)
    print('Improvement: ',
          round((initial_cost - min_cost) / initial_cost, 4) * 100, '%')

    return [min_cost, best_solution]

# chlodzenie
def cool(t, type):
    if type == "linear":
        new_temp = t + ((stopping_temp - temp) / stopping_iter)  # liniowy Cauchy'ego
    elif type == "log":
        new_temp = t / (1 + (
                    ((temp - stopping_temp) / (stopping_iter * stopping_temp * temp)) * t))  # logarytmiczny, boltzmana
    else:
        new_temp = t * ((stopping_temp/temp) ** (1/stopping_iter))  # geometryczny
        # new_temp = t * alpha  # geometryczny

    return new_temp


# wylicza początkowe rozwiazanie za pomocą strategi najbliższego sasiada
def getFirstSolution(matrix):
    node = 0
    result = [node]

    nodes_to_visit = list(range(len(matrix)))
    nodes_to_visit.remove(node)

    while nodes_to_visit:
        nearest_node = min([(matrix[node][j], j) for j in nodes_to_visit], key=lambda x: x[0])
        node = nearest_node[1]
        nodes_to_visit.remove(node)
        result.append(node)

    return result


# get config from config.ini file
def getConfig():
    file = open("config.ini", "r")
    config = []
    for line in file.readlines():
        if line.find('.csv') > 1:
            global outputFile
            outputFile = line
            break

        tmp = line.split(maxsplit=3)
        config.append({'file': tmp[0], 'repetitions': tmp[1], 'cost': tmp[2], 'path': tmp[3]})

    return config


def group(cooling_type, neighbourhood_type):
    config = getConfig()
    new = {}

    with open(outputFile, 'a', newline='') as csvfile:
        fieldnames = ['file', 'repetitions', 'cost', 'time', 'diff', 'cooling', 'neighbour', 'path']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_NONE)
        writer.writeheader()

        for item in config:
            data = getDataAndConvert(item['file'])
            matrix = data[0]
            repetitions = int(item['repetitions'])

            if repetitions:
                writer.writerow({'file': item['file'], 'repetitions': repetitions, 'cost': item['cost'],
                                 'cooling': cooling_type, 'neighbour' : neighbourhood_type, 'path': item['path'].strip('\n')})

                for tmp in range(repetitions):
                    begin = timeit.default_timer()
                    results = solve(matrix, temp, stopping_temp, stopping_iter, cooling_type, neighbourhood_type)
                    end = timeit.default_timer()

                    print('time: ' + results[0].__str__())

                    best_cost = float(item['cost'])
                    diff = (results[0] - best_cost) / best_cost * 100

                    writer.writerow(
                        {'cost': round(results[0], 0), 'path': str(results[1]).strip(",0"),
                         'time': round((end - begin), 3), 'diff': round(diff, 3)})

                    new[item['file']] = {'file': item['file'], 'repetitions': repetitions, 'cost': results[0],
                                         'path': str(results[1]).strip(",0"), 'time': round((end - begin), 5)}


# def one():
#     temp = 1000
#     stopping_temp = 0.00000001
#     alpha = 0.9999
#     stopping_iter = 10000000000
#     filename = "testData/a280.tsp.txt"
#     file = open(filename, 'r')
#     a = []
#     b = []
#
#     for line in file.readlines():
#         line = line.split()
#         if len(line) > 1:
#             tmp = parseStringstoIntegers(line)
#             a.append(tmp[1])
#             b.append(tmp[2])
#
#     coords = numpy.column_stack((a, b))
#
#     matrix = numpy.sqrt((numpy.square(coords[:, numpy.newaxis] - coords).sum(axis=2)))
#
#     begin = timeit.default_timer()
#     results = solve(matrix, temp, alpha, stopping_temp, stopping_iter)
#     end = timeit.default_timer()
#
#     print(results)
#     print(end - begin)


def main():
    global stopping_temp, temp, stopping_iter, alpha
    temp = 1  # temperatura startu 1
    stopping_temp = 0.01  # temperatura zatrzymujaca algorytm 0.01
    stopping_iter = 100000  # liczba iteracji zatrzymujaca algorytm 100000
    alpha = ((stopping_temp/temp) ** (1/stopping_iter))

    group("linear", "insert")
    group("log", "insert")
    group("geometric", "insert")

    group("linear", "2opt")
    group("log", "2opt")
    group("geometric", "2opt")


main()
