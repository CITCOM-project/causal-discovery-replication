def program_node_10_edge_50(
	X1: int,
	X2: int,
	Y1: int = None,
	Y2: int = None,
	Y3: int = None,
	Y4: int = None,
	Y5: int = None,
	Y6: int = None,
	Y7: int = None,
	Y8: int = None,
):
	"""Causal structure:
		('X1', 'Y1')
		('X1', 'Y2')
		('X1', 'Y3')
		('X1', 'Y4')
		('X1', 'Y6')
		('X1', 'Y7')
		('X1', 'Y8')
		('Y1', 'Y3')
		('Y1', 'Y6')
		('Y1', 'Y7')
		('Y2', 'Y4')
		('Y2', 'Y6')
		('Y2', 'Y8')
		('Y3', 'Y4')
		('Y3', 'Y5')
		('Y3', 'Y6')
		('Y3', 'Y7')
		('Y4', 'Y7')
		('Y6', 'Y7')
		('Y6', 'Y8')
		('X2', 'Y3')
		('X2', 'Y4')
		('X2', 'Y6')
		('Y5', 'Y6')
		('Y5', 'Y7')
	"""
	if Y1 is None:
		Y1 = (-1 * X1) + 4
	if Y2 is None:
		Y2 = (-1 * X1) + -7
	if Y3 is None:
		Y3 = (-9 * X1) + (7 * Y1) + (-9 * X2) + -7
	if Y4 is None:
		Y4 = (-4 * X1) + (10 * Y2) + (-6 * Y3) + (5 * X2) + -2
	if Y5 is None:
		Y5 = (-3 * Y3) + 6
	if Y6 is None:
		Y6 = (-5 * X1) + (-2 * Y1) + (10 * Y2) + (7 * Y3) + (-5 * X2) + (4 * Y5) + 10
	if Y7 is None:
		Y7 = (-3 * X1) + (7 * Y1) + (-10 * Y3) + (10 * Y4) + (-6 * Y6) + (10 * Y5) + 3
	if Y8 is None:
		Y8 = (7 * X1) + (-2 * Y2) + (-10 * Y6) + -5
	return {'Y1': Y1, 'Y2': Y2, 'Y3': Y3, 'Y4': Y4, 'Y5': Y5, 'Y6': Y6, 'Y7': Y7, 'Y8': Y8}
