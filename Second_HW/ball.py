import math

class ball():
    def __init__(ball, color, size, position, velocity):
        ball.color = color
        ball.size = size
        ball.position = position
        ball.velocity = velocity
        ball.speed = (velocity[0] ** 2 + velocity[1] ** 2) ** 0.5

    def move(ball):
        ball.position = (int(ball.position[0] + ball.velocity[0]), int(ball.position[1] + ball.velocity[1]))
        return ball.position

    def Change_Dir(ball, unit_dir_of_obst):
    
        projection_onto = unit_dir_of_obst[0] * ball.velocity[0] + unit_dir_of_obst[1] * ball.velocity[1]
        # positon of - in taking normal of the obstacle is adjusted for opencv frame since it is starts from top left 
        projection_normal = -unit_dir_of_obst[1] * ball.velocity[0] + unit_dir_of_obst[0] * ball.velocity[1]

        obst_angle = math.atan2(unit_dir_of_obst[1], unit_dir_of_obst[0])
        dep_angle = obst_angle + math.atan2(-projection_normal, projection_onto)

        ball.velocity = (math.cos(dep_angle) * ball.speed, math.sin(dep_angle) * ball.speed)

        return ball.velocity, projection_onto, projection_normal, dep_angle, obst_angle


