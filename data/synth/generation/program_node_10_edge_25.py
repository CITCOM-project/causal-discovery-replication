def program_node_10_edge_25(
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
):
	"""Causal structure:
		('X1', 'Y2')
		('X1', 'Y3')
		('X1', 'Y4')
		('X1', 'Y5')
		('Y3', 'Y4')
		('X2', 'Y1')
		('Y1', 'Y4')
		('X3', 'Y2')
		('X4', 'Y3')
		('X5', 'Y4')
	"""
	if Y1 is None:
		Y1 = (10 * X2) + 6
	if Y3 is None:
		Y3 = (4 * X1) + (-5 * X4) + -2
	if Y2 is None:
		Y2 = (10 * X1) + (-6 * X3) + 9
	if Y4 is None:
		Y4 = (-10 * X1) + (-5 * Y3) + (-3 * Y1) + (7 * X5) + -10
	if Y5 is None:
		Y5 = (7 * X1) + -2
	return {'Y1': Y1, 'Y2': Y2, 'Y3': Y3, 'Y4': Y4, 'Y5': Y5}
