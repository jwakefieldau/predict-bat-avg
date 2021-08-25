import sys

from csv import DictWriter

from cricinfo import Player

result_index = None
output_path = None

if len(sys.argv) == 4:
	result_index = int(sys.argv[2])
	output_path = sys.argv[3]
if len(sys.argv) == 2 or len(sys.argv) == 4:
	search_name = sys.argv[1]
else:
	sys.stderr.write(f"Usage: {sys.argv[0]} search_name result_index output_path\r\n")	
	sys.exit(1)

players = Player.player_search(search_name)
print(f"search returned {len(players)} results")

for (i, enum_player,) in enumerate(players):
	if (result_index is not None) and (result_index == i):
		print(f'**{i}:{enum_player}')
	else:
		print(f'{i}:{enum_player}')

if (result_index is not None) and output_path:
	with open(output_path, 'wt') as f:
		p = players[result_index]
		p.get_match_summaries_career_stats('test')
		test_match_stats_list = p.match_list_stats_dict['test']
		dw = DictWriter(f, fieldnames=vars(test_match_stats_list[0]).keys())

		dw.writeheader()
		for test_match_stats in test_match_stats_list:
			dw.writerow(vars(test_match_stats))

	print(f'Wrote {len(test_match_stats_list)} rows')
