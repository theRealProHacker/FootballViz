def goal_per_money(goals,money):
    if 0 in (goals,money): 
        return 0
    else:
        return goals/money * 1000000 #goals per 1000000 € spent

def points_per_goal(points, goals):	
    if not points*goals:
        return 0
    else:
        return goals/points #goals per point

def points_per_money(points,money):
    if 0 in (points,money):
        return 0
    else:
        return points/money * 1000000 #points per 1000000 € spent

def goals_against_per_point(goals_against,points):
    if 0 in (goals_against,points):
        return 0
    else:
        return goals_against/points # goals_against per point
