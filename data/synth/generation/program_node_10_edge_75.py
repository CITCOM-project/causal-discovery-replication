def program_node_10_edge_75(
	X1: int,
	Y1: int = None,
	Y2: int = None,
	Y3: int = None,
	Y4: int = None,
	Y5: int = None,
	Y6: int = None,
	Y7: int = None,
	Y8: int = None,
	Y9: int = None,
):
	"""Causal structure:
		('X1', 'Y1')
		('X1', 'Y2')
		('X1', 'Y4')
		('X1', 'Y5')
		('X1', 'Y6')
		('X1', 'Y7')
		('X1', 'Y8')
		('X1', 'Y9')
		('Y1', 'Y3')
		('Y1', 'Y4')
		('Y1', 'Y7')
		('Y1', 'Y8')
		('Y1', 'Y9')
		('Y2', 'Y4')
		('Y2', 'Y5')
		('Y2', 'Y6')
		('Y2', 'Y7')
		('Y2', 'Y8')
		('Y2', 'Y9')
		('Y4', 'Y5')
		('Y4', 'Y6')
		('Y4', 'Y7')
		('Y4', 'Y8')
		('Y5', 'Y8')
		('Y5', 'Y9')
		('Y6', 'Y7')
		('Y6', 'Y8')
		('Y7', 'Y8')
		('Y7', 'Y9')
		('Y8', 'Y9')
		('Y3', 'Y4')
		('Y3', 'Y5')
		('Y3', 'Y7')
		('Y3', 'Y8')
	"""
	if Y1 is None:
		Y1 = (-9 * X1) + -5
	if Y2 is None:
		Y2 = (-3 * X1) + -5
	if Y3 is None:
		Y3 = (-8 * Y1) + 9
	if Y4 is None:
		Y4 = (-6 * X1) + (-8 * Y1) + (-1 * Y2) + (-2 * Y3) + 8
	if Y5 is None:
		Y5 = (-3 * X1) + (10 * Y2) + (-1 * Y4) + (5 * Y3) + 4
	if Y6 is None:
		Y6 = (-2 * X1) + (-9 * Y2) + (7 * Y4) + -9
	if Y7 is None:
		Y7 = (4 * X1) + (-8 * Y1) + (6 * Y2) + (-4 * Y4) + (10 * Y6) + (-6 * Y3) + 4
	if Y8 is None:
		Y8 = (10 * X1) + (-6 * Y1) + (10 * Y2) + (4 * Y4) + (-5 * Y5) + (-2 * Y6) + (10 * Y7) + (7 * Y3) + -5
	if Y9 is None:
		Y9 = (7 * X1) + (-2 * Y1) + (-10 * Y2) + (-5 * Y5) + (-3 * Y7) + (7 * Y8) + -10
	return {'Y1': Y1, 'Y2': Y2, 'Y3': Y3, 'Y4': Y4, 'Y5': Y5, 'Y6': Y6, 'Y7': Y7, 'Y8': Y8, 'Y9': Y9}
