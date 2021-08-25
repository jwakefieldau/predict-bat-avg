# read csv data and build a cumulative table of averages
# based only on innings where batsman was dismissed
# ie: if batsman dismissed for n, then that score
# helps determine average when dismissed for >= 0, >= 1,
# >= 2, ..., >= n.

# then, with "at least" dismissed score values on x axis
# and average score values on y axis, fit a curve, ideally for
# 0 <= x >= 400

# we can later use this to predict dismissed score from not out
# score
import sys
import csv

from csv import DictReader

import numpy

from scipy.optimize import curve_fit

file_path = sys.argv[1]

def str_to_bool(val):
	if val == 'True':
		return True
	elif val == 'False':
		return False
	elif val == 'None' or val == '':
		return None
	else:
		raise ValueError(f"Cannot convert '{val}' to bool")

def add_score_to_lists(score, score_gte_lists):

	for n in range(score + 1):
		score_gte_lists[n].append(score)

def load_scores(file_path):

	top_not_out_score = 0

	# for each feasible score n, maintain a list of scores >= n
	# the list returned will be trimmed down to the top not out score
	# as that's the highest one we need to predict
	score_gte_lists = []

	# also track all out and not out scores for predictive average 
	# calculation later
	out_score_list = []
	not_out_score_list = []

	for n in range(600):
		score_gte_lists.append([])

	with open(file_path, 'rt') as f:
		for row in DictReader(f):

			try:
				first_innings_score = int(row['first_innings_score'])
			except (ValueError, TypeError) as e:
				first_innings_score = None
			first_innings_not_out = str_to_bool(row['first_innings_not_out'])

			if first_innings_score is not None:
				if first_innings_not_out == True:
					if first_innings_score > top_not_out_score:
						top_not_out_score = first_innings_score
					not_out_score_list.append(first_innings_score)

				elif first_innings_not_out == False:
					add_score_to_lists(first_innings_score, score_gte_lists)
					out_score_list.append(first_innings_score)

			try:
				second_innings_score = int(row['second_innings_score'])
			except (ValueError, TypeError) as e:
				second_innings_score = None
			second_innings_not_out = str_to_bool(row['second_innings_not_out'])

			if second_innings_score is not None:
				if second_innings_not_out == True:
					if second_innings_score > top_not_out_score:
						top_not_out_score = second_innings_score
					not_out_score_list.append(second_innings_score)

				elif second_innings_not_out == False:
					add_score_to_lists(second_innings_score, score_gte_lists)
					out_score_list.append(second_innings_score)

	# trim score_gte_lists down to top_not_out_score
	ret_score_gte_lists = [score_gte_lists[n] for n in range(top_not_out_score + 1)]

	return (ret_score_gte_lists, out_score_list, not_out_score_list,)
			
def score_gte_avgs(score_gte_lists):

	avgs_list = [None] * len(score_gte_lists)

	for (i, score_gte_list,) in enumerate(score_gte_lists):
		cur_agg_runs = sum(score_gte_list)
		cur_dismissed = len(score_gte_list)
		cur_avg = float(cur_agg_runs / cur_dismissed) if cur_dismissed > 0 else None
		avgs_list[i] = cur_avg

	return avgs_list

def write_avgs_list(avgs_list, fit_avgs_list, avgs_list_file_path):
	with open(avgs_list_file_path, 'wt') as f:
		csv_avgs = csv.writer(f)
		for ((i, avg,), fit_avg,) in zip(enumerate(avgs_list), fit_avgs_list,):
			csv_avgs.writerow([i, avg, fit_avg])

def prediction_func(x, a, b):
	return (a * x) + b

# find parameter values for curve with
# optimal fit, return a list of average values from the 
# fitted curve
#TODO - figure out how to have a curve shaped like this but where y>=x
#it makes no sense that a not out score of x predicts a score y<x
def do_fit(avgs_list):

	#def func(x, a, b, c, d):
		#return a * numpy.log((b * x) + c) + (x + d)

	#def func(x, a, b, c, d, e, f):
		#return (a * (x ** 5)) + (b * (x ** 4)) + (c * (x ** 3)) + (d * (x ** 2)) + (e * x) + f

	# only include x data where we have values
	fit_xdata = [x for x in range(len(avgs_list)) if avgs_list[x] is not None]
	fit_ydata = [y for y in avgs_list if y is not None]

	# argument to log must be >= 0
	#param_lower_bounds = [-numpy.inf, 0, 0, -numpy.inf]
	#param_upper_bounds = [numpy.inf, numpy.inf, numpy.inf, numpy.inf]

	# y must be >x
	param_lower_bounds = [1, 0]
	param_upper_bounds = [numpy.inf, numpy.inf]

  # figure out how to make y >= x
	#param_lower_bounds = [-numpy.inf, -numpy.inf, -numpy.inf, -numpy.inf, -numpy.inf, -numpy.inf]
	#param_upper_bounds = [numpy.inf, numpy.inf, numpy.inf, numpy.inf, numpy.inf, numpy.inf]


	(fit_params, _) = curve_fit(prediction_func, fit_xdata, fit_ydata, bounds=(param_lower_bounds, param_upper_bounds,))

	#(a, b, c, d,) = fit_params
	(a, b,) = fit_params
	#(a, b, c, d, e, f,) = fit_params

	return (a, b,)

def calc_and_write_output(out_score_list, not_out_score_list, a, b, out_file_path):

	# calculate traditional average and predicted average, but
	# not outs are replaced by predicted dismissed scores.
	with open(out_file_path, 'wt') as out_f:

		out_f.write(f'not out prediction function = y = {a}x + {b}\r\n')

		pred_score_sum = 0
		for not_out_score in not_out_score_list:
			pred_score = round(prediction_func(not_out_score, a, b)) 

			out_f.write(f'predicted {pred_score}, out from {not_out_score} not out\r\n')

			pred_score_sum += pred_score

		total_runs_with_pred = sum(out_score_list) + pred_score_sum
		total_inns = len(out_score_list) + len(not_out_score_list)
		pred_avg = float(total_runs_with_pred / total_inns)

		total_runs = sum(out_score_list) + sum(not_out_score_list)
		total_outs = len(out_score_list)
		trad_avg = float(total_runs / total_outs)
		
		out_f.write(f'predicted {total_runs_with_pred} total runs in {total_inns} innings for {pred_avg} predicted average\r\n')
		out_f.write(f'actual {total_runs} total runs with {total_outs} dismissals for {trad_avg} average\r\n')

		return (trad_avg, pred_avg,)

if __name__ == '__main__':
	data_file_path = sys.argv[1]
	fit_file_path = sys.argv[2]
	out_file_path = sys.argv[3]

	(score_gte_lists, out_score_list, not_out_score_list,) = load_scores(data_file_path)
	avgs_list = score_gte_avgs(score_gte_lists)
	(a, b,) = do_fit(avgs_list)
	fit_avgs_list = [prediction_func(x, a, b) for x in range(len(avgs_list))]
	write_avgs_list(avgs_list, fit_avgs_list, fit_file_path)
	calc_and_write_output(out_score_list, not_out_score_list, a, b, out_file_path)

# verify we've got this right so far, then move on to plotting
# so we can consider what type of curve we're dealing with