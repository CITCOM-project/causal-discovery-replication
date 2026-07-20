def program_node_20_edge_25(
	X1: int,
	X2: int,
	X3: int,
	X4: int,
	X5: int,
	Y1: int = None,
	Y2: int = None,
	Y3: int = None,
	Y4: int = None,
	Y5: int = None,
	Y6: int = None,
	Y7: int = None,
	Y8: int = None,
	Y9: int = None,
	Y10: int = None,
	Y11: int = None,
	Y12: int = None,
	Y13: int = None,
	Y14: int = None,
	Y15: int = None,
):
	"""Causal structure:
		('X1', 'Y2')
		('X1', 'Y4')
		('X1', 'Y5')
		('X1', 'Y6')
		('X1', 'Y9')
		('Y2', 'Y4')
		('Y2', 'Y14')
		('Y2', 'Y15')
		('Y4', 'Y6')
		('Y4', 'Y10')
		('Y5', 'Y7')
		('Y5', 'Y11')
		('Y5', 'Y15')
		('Y6', 'Y13')
		('Y6', 'Y14')
		('X2', 'Y1')
		('X2', 'Y6')
		('X2', 'Y7')
		('X2', 'Y11')
		('Y1', 'Y3')
		('Y1', 'Y6')
		('Y1', 'Y11')
		('Y1', 'Y14')
		('Y7', 'Y10')
		('Y7', 'Y14')
		('X3', 'Y3')
		('X3', 'Y7')
		('X3', 'Y8')
		('X3', 'Y14')
		('Y3', 'Y5')
		('Y3', 'Y6')
		('Y3', 'Y11')
		('Y8', 'Y9')
		('Y8', 'Y10')
		('Y8', 'Y12')
		('X4', 'Y2')
		('X4', 'Y6')
		('X4', 'Y8')
		('X4', 'Y10')
		('X5', 'Y15')
	"""
	if Y1 is None:
		Y1 = (7 * X2) + -7
	if Y2 is None:
		Y2 = (8 * X1) + (5 * X4) + 0
	if Y3 is None:
		Y3 = (-6 * Y1) + (-7 * X3) + -5
	if Y4 is None:
		Y4 = (4 * X1) + (-7 * Y2) + 10
	if Y5 is None:
		Y5 = (-10 * X1) + (-1 * Y3) + 0
	if Y6 is None:
		Y6 = (-10 * X1) + (6 * Y4) + (-10 * X2) + (-6 * Y1) + (-8 * Y3) + (-1 * X4) + 7
	if Y7 is None:
		Y7 = (8 * Y5) + (-10 * X2) + (-6 * X3) + 2
	if Y8 is None:
		Y8 = (-2 * X3) + (-3 * X4) + 2
	if Y9 is None:
		Y9 = (7 * X1) + (-9 * Y8) + 2
	if Y10 is None:
		Y10 = (1 * Y4) + (10 * Y7) + (-5 * Y8) + (-8 * X4) + 5
	if Y11 is None:
		Y11 = (-5 * Y5) + (-6 * X2) + (-4 * Y1) + (-6 * Y3) + 10
	if Y12 is None:
		Y12 = (5 * Y8) + -5
	if Y13 is None:
		Y13 = (2 * Y6) + 9
	if Y14 is None:
		Y14 = (5 * Y2) + (3 * Y6) + (-7 * Y1) + (-7 * Y7) + (-1 * X3) + 2
	if Y15 is None:
		Y15 = (-7 * Y2) + (1 * Y5) + (-7 * X5) + 1
	return {'Y1': Y1, 'Y2': Y2, 'Y3': Y3, 'Y4': Y4, 'Y5': Y5, 'Y6': Y6, 'Y7': Y7, 'Y8': Y8, 'Y9': Y9, 'Y10': Y10, 'Y11': Y11, 'Y12': Y12, 'Y13': Y13, 'Y14': Y14, 'Y15': Y15}
