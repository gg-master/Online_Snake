import pygame
from classes import Client

pygame.init()
font_fps = pygame.font.SysFont("Arial", 18)


def update_fps(cl):
    fps = str(int(cl.get_fps()))
    fps_text = font_fps.render(fps, True, pygame.Color("coral"))
    return fps_text


def main():
    global screen, fullscreen
    running = True
    clock = pygame.time.Clock()
    client = Client(screen)
    while running:

        screen.fill(pygame.Color('black'))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.VIDEORESIZE:
                if not fullscreen:
                    screen = pygame.display.set_mode((event.w, event.h),
                                                     pygame.RESIZABLE)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    pass
                    # fullscreen = not fullscreen
                    # if fullscreen:
                    #     screen = pygame.display.set_mode(monitor_size,
                    #                                      pygame.FULLSCREEN)
                    # else:
                    #     screen = pygame.display.set_mode(
                    #         (screen.get_width(), screen.get_height()),
                    #         pygame.RESIZABLE)
            client.update(event)
        else:
            client.update()

        client.render(screen)

        screen.blit(update_fps(clock), (10, 0))
        # if pygame.mouse.get_focused():
        #     client.cursor.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()
# 1 Snake False - False // 1: Snake True - 1629224450/2: Snake True - 1629221070
# 2 Snake False - False // 1: Snake True - 1629224450/2: Snake True - 1629221070
# 1 Snake False - False // 1: Snake False - 1629224450/2: Snake False - False
# 2 Snake False - False // 1: Snake False - 1629224450/2: Snake False - False

# 1 Snake False - False // 1: Snake False - 1629224450/2: Snake False - False
# 2 Snake False - False // 1: Snake False - 1629224450/2: Snake False - False
# 1 Snake True - 1629224455 // 1: Snake False - 1629224450/2: Snake False - False
# 2 Snake True - False // 1: Snake False - 1629224450/2: Snake False - False

if __name__ == '__main__':
    WIDTH, HEIGHT = 950, 750
    FPS = 30
    # screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    monitor_size = [pygame.display.Info().current_w,
                    pygame.display.Info().current_h]
    # background = pygame.Surface((WIDTH, HEIGHT))
    fullscreen = False
    main()
