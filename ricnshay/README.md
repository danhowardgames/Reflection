# Ric 'n' Shay

A top-down laser ricochet game where you control two characters to defeat enemies by bouncing lasers off of your assistant robot.

## Description

In this game, you control Ric, a character who can fire lasers at Shay, a helper robot. The lasers ricochet off Shay in a direction that you can control. Use this mechanic to hit enemies from their vulnerable angles while avoiding direct contact with them.

## Game Mechanics

- **Ric (Player 1)**: Moves with WASD and fires lasers with SPACE
- **Shay (Assistant Robot)**: Follows mouse cursor and acts as a ricochet point
- **Laser Ricochet**: Modify the ricochet angle with Q and E (±22.5° increments)
- **Enemies**: Only vulnerable from specific angles, move toward Ric
- **Waves**: 5 waves of increasing difficulty, with more and faster enemies each wave

## Controls

- **W, A, S, D**: Move Ric
- **Mouse**: Control Shay's position
- **Q**: Rotate ricochet angle counter-clockwise (22.5°)
- **E**: Rotate ricochet angle clockwise (22.5°)
- **SPACE**: Fire laser from Ric toward Shay
- **R**: Restart game after Game Over or Victory
- **F1**: Toggle debug mode (if enabled)

## Installation

1. Ensure you have Python 3.10+ installed
2. Install the required dependencies: `pip install pygame`
3. Run the game: `python main.py`

## Debug Controls (Only in Debug Mode)

- **F1**: Toggle debug mode
- **F**: Skip current wave
- **G**: Toggle god mode (infinite health)

## Game Elements

- **Ric**: Blue square character with 3 health points
- **Shay**: Green square robot that follows your mouse 
- **Laser**: Red beam that ricochets off Shay
- **Enemies**: Colored squares with a direction indicator, vulnerable from their back
- **Walls**: Gray blocks that block movement and lasers

## Strategy Tips

- Position Shay strategically to create useful ricochet angles
- Modify the ricochet angle to hit enemies from their vulnerable sides
- Keep moving to avoid being hit by enemies
- Use the obstacles as protection from enemies

## Technical Details

- Built with Python 3.10+ and Pygame 2.0+
- Uses raycast for laser collision detection
- Features angle-based vulnerability detection

Enjoy the game! 