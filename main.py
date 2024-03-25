# TODO: there are some circumstances in which the computer will hit part of a ship but not the
# rest. Later, the computer will hit that ship, and once it starts moving in the correct
# direction it will reach the spot where it had hit and it will fail to continue. Make it skip
# two spaces instead of one to continue hitting the ship
import atexit
from time import sleep
import random
import pygame
from pygame.locals import MOUSEBUTTONDOWN, QUIT
# Each square has a corresponding tile class
class Tile(pygame.sprite.Sprite):
  # Types: E: Empty, H: Hit, M: Miss, S: Ship, s: Damaged ship
  def __init__(self, surf, x, y):
    super(Tile, self).__init__()
    self.type = "E"
    self.rect = pygame.Rect(x, y, 20, 20)
    self.surf = surf
  def setType(self, t):
    if t in ("E", "H", "M", "S", "s"):
      self.type = t
  def draw(self):
    if self.type == "s":
      pygame.draw.rect(self.surf, (191, 191, 191), self.rect)
      pygame.draw.rect(self.surf, (255, 0, 0), pygame.Rect(self.rect.x + 5, self.rect.y + 5, 10, 10))
      color = None
    elif self.type == "E":
      color = None
    elif self.type == "H":
      color = (255, 0, 0)
    elif self.type == "M":
      color = (255, 255, 255)
    elif self.type == "S":
      color = (191, 191, 191)
    if color is not None:
      pygame.draw.rect(self.surf, color, self.rect)
    pygame.draw.rect(self.surf, (255, 255, 255), self.rect, 1)
class Opponent:
  def __init__(self):
    global allPositions
    self.shipPositions = []
    self.shotPositionsRemaining = allPositions
    self.shipPositionsRemaining = allPositions
    self.prevShot = None
    self.shotDirection = None
    self.testingDirections = False
    self.destroying = False
    self.attemptingRestart = False
    self.tryAgain = False
    self.destroyingShots = []
    self.possibleShotDirections = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    self.aircraftCarrierPositions = []
    self.battleshipPositions = []
    self.cruiserPositions = []
    self.submarinePositions = []
    self.destroyerPositions = []
    self.sinks = 0
    # Place all the ships
    self.failed = False
    self.placeShip(5, self.aircraftCarrierPositions)
    while self.failed:
      self.placeShip(5, self.aircraftCarrierPositions)
    self.failed = False
    self.placeShip(4, self.battleshipPositions)
    while self.failed:
      self.placeShip(4, self.battleshipPositions)
    self.failed = False
    self.placeShip(3, self.cruiserPositions)
    while self.failed:
      self.placeShip(3, self.cruiserPositions)
    self.failed = False
    self.placeShip(3, self.submarinePositions)
    while self.failed:
      self.placeShip(3, self.submarinePositions)
    self.failed = False
    self.placeShip(2, self.destroyerPositions)
    while self.failed:
      self.placeShip(2, self.destroyerPositions)
  def placeShip(self, length, positionsVariable):
    directions = ((0, 1), (0, -1), (1, 0), (-1, 0))
    p1 = random.sample(self.shipPositionsRemaining, 1)[0]
    positionsVariable.append(p1)
    self.shipPositions.append(p1)
    directionsLeft = random.sample(directions, 4)
    finDirection = None
    # Chooses a legal direction to commit to
    for direction in directionsLeft:
      inBounds = True
      p2 = p1
      for i in range(length - 1):
        p2 = (p2[0] + direction[0], p2[1] + direction[1])
        if p2 in self.shipPositions:
          inBounds = False
          break
        if p2[0] < 0 or p2[0] > 9 or p2[1] < 0 or p2[1] > 9:
          inBounds = False
          break
      if inBounds:
        finDirection = direction
        break
    if finDirection is None:
      # It failed
      self.failed = True
      self.shipPositions.remove(p1)
      positionsVariable.remove(p1)
      self.shipPositionsRemaining.remove(p1)
    else:
      # It succeeded; place the ship
      for i in range(length - 1):
        self.shipPositionsRemaining.remove(p1)
        p1 = (p1[0] + finDirection[0], p1[1] + finDirection[1])
        positionsVariable.append(p1)
        self.shipPositions.append(p1)
  def attack(self):
    # Don't put your ships together or it will probably get really confused
    global hitTiles, running, text
    # If it hasn't fired yet, shoot randomly
    if self.prevShot is None:
      shot = random.sample(self.shotPositionsRemaining, 1)[0]
      self.processShot(shot)
    elif self.destroying:
      # If it knows the position of a certain ship
      if self.prevShot["result"] == "miss":
        if not self.attemptingRestart:
          # Going to try to go the other way from the first shot position that hit
          self.attemptingRestart = True
          self.shotDirection = (-self.shotDirection[0], -self.shotDirection[1])
          shot = (self.destroyingShots[0][0] + self.shotDirection[0], self.destroyingShots[0][1] + self.shotDirection[1])
          self.processShot(shot)
          if self.tryAgain:
            self.tryAgain = False
            # Going the other way didn't work... It must not have actually been a ship... shoot randomly
            # TODO: lets actually choose previous hits and shoot around there
            self.attemptingRestart = False
            self.destroying = False
            self.shotDirection = None
            self.destroyingShots = []
            shot = random.sample(self.shotPositionsRemaining, 1)[0]
            self.processShot(shot)
        else:
          # Going the other way didn't work... It must not have actually been a ship... shoot randomly
          # TODO: lets actually choose previous hits and shoot around there
          self.attemptingRestart = False
          self.destroying = False
          self.shotDirection = None
          self.destroyingShots = []
          shot = random.sample(self.shotPositionsRemaining, 1)[0]
          self.processShot(shot)
      elif self.prevShot["result"] == "sink":
        self.destroying = False
        self.shotDirection = None
        self.destroyingShots = []
        shot = random.sample(self.shotPositionsRemaining, 1)[0]
        self.processShot(shot)
      else:
        # Keep shooting in the expected direction that the ship exists
        position = self.prevShot["position"]
        shot = (position[0] + self.shotDirection[0], position[1] + self.shotDirection[1])
        self.processShot(shot)
        if self.tryAgain:
          self.tryAgain = False
          # Treat this like we missed after firing without sinking; going to try to go the other way from the first shot position that hit
          self.attemptingRestart = True
          self.shotDirection = (-self.shotDirection[0], -self.shotDirection[1])
          shot = (self.destroyingShots[0][0] + self.shotDirection[0], self.destroyingShots[0][1] + self.shotDirection[1])
          self.processShot(shot)
          if self.tryAgain:
            self.tryAgain = False
            # Going the other way wasn't possible... It must not have actually been a ship... shoot randomly
            self.attemptingRestart = False
            self.destroying = False
            self.shotDirection = None
            self.destroyingShots = []
            shot = random.sample(self.shotPositionsRemaining, 1)[0]
            self.processShot(shot)
    elif self.prevShot["result"] == "hit" or self.testingDirections:
      # Found a new ship!
      # Is it already found?
      if not self.testingDirections:
        # Assert the existence of a previously unknown ship
        position = self.prevShot["position"]
        self.destroyingShots.append(position)
        self.testingDirections = True
      try:
        # Keep looking for a legal direction in which to fire
        legal = False
        while not legal:
          # Test the legality of a direction
          direction = random.sample(self.possibleShotDirections, 1)[0]
          self.possibleShotDirections.remove(direction)
          shot = (self.destroyingShots[0][0] + direction[0], self.destroyingShots[0][1] + direction[1])
          if shot in self.shotPositionsRemaining and not shot[0] < 0 and not shot[0] > 9 and not shot[1] < 0 and not shot[1] > 9:
            legal = True
        # Fire
        self.processShot(shot)
        while self.tryAgain:
          self.tryAgain = False
          legal = False
          while not legal:
            # Test the legality of a direction
            direction = random.sample(self.possibleShotDirections, 1)[0]
            self.possibleShotDirections.remove(direction)
            shot = (self.destroyingShots[0][0] + direction[0], self.destroyingShots[0][1] + direction[1])
            if shot in self.shotPositionsRemaining and not shot[0] < 0 and not shot[0] > 9 and not shot[1] < 0 and not shot[1] > 9:
              legal = True
          # Fire
          self.processShot(shot)
        if self.prevShot["result"] == "hit":
          # The shot was successful!
          # Set the predicted direction in which the ship exists
          self.possibleShotDirections = [(0, 1), (0, -1), (1, 0), (-1, 0)]
          self.testingDirections = False
          self.shotDirection = direction
          self.destroying = True
      except ValueError:
        # What happened is that a hit was scored on a ship that had been partially destroyed. This particular place was surrounded by previous shots, so it would be illegal to test directions
        # Shoot randomly
        # TODO: if algorithm notices that it has partially destroyed ships, keep shooting at them! (see lines 1, 132, 141)
        self.attemptingRestart = False
        self.destroying = False
        self.shotDirection = None
        self.destroyingShots = []
        shot = random.sample(self.shotPositionsRemaining, 1)[0]
        self.processShot(shot)
    else:
      # Missed; keep shooting randomly
      shot = random.sample(self.shotPositionsRemaining, 1)[0]
      self.processShot(shot)
  def processShot(self, shot):
    global aircraftCarrierPositions, battleshipPositions, cruiserPositions, submarinePositions, destroyerPositions, text, running, hitTiles
    try:
      self.shotPositionsRemaining.remove(shot)
    except ValueError:
      # The shot wasn't legal! Try again.
      self.tryAgain = True
      return
    result = None
    if shot in aircraftCarrierPositions:
      if len(aircraftCarrierPositions) == 1:
        result = "sink"
      else:
        result = "hit"
      aircraftCarrierPositions.remove(shot)
    elif shot in battleshipPositions:
      if len(battleshipPositions) == 1:
        result = "sink"
      else:
        result = "hit"
      battleshipPositions.remove(shot)
    elif shot in cruiserPositions:
      if len(cruiserPositions) == 1:
        result = "sink"
      else:
        result = "hit"
      cruiserPositions.remove(shot)
    elif shot in submarinePositions:
      if len(submarinePositions) == 1:
        result = "sink"
      else:
        result = "hit"
      submarinePositions.remove(shot)
    elif shot in destroyerPositions:
      if len(destroyerPositions) == 1:
        result = "sink"
      else:
        result = "hit"
      destroyerPositions.remove(shot)
    else:
      # We didn't hit any of the ships; declare it a miss
      result = "miss"
      hitTiles[shot[1]][shot[0]].setType("M")
    if result in ("hit", "sink"):
      # Render the ship as hit
      hitTiles[shot[1]][shot[0]].setType("s")
    if result == "sink":
      # We are one ship closer to winning
      self.sinks += 1
    if self.sinks == 5:
      # The player loses
      text = "You lose!"
      draw()
      running = False
      return
    self.prevShot = {
      "result": result,
      "position": shot
    }
def pollClicks(setFlag = 0):
  # The setFlag variable represents which allowed data sets to poll clicks from
  global lastClickPos, prevClickPos
  while lastClickPos == prevClickPos:
    for event in pygame.event.get():
      if event.type == MOUSEBUTTONDOWN:
        if setFlag == 0 or setFlag == 1:
          for i in shotTiles:
            for j in i:
              if j.rect.collidepoint(event.pos):
                lastClickPos = (event.pos[0] // 20, event.pos[1] // 20)
        if setFlag == 0 or setFlag == 2:
          for i in hitTiles:
            for j in i:
              if j.rect.collidepoint(event.pos):
                lastClickPos = (event.pos[0] // 20, event.pos[1] // 20)
  prevClickPos = lastClickPos
def draw():
  global shotTiles, hitTiles
  pygame.draw.rect(surf, (0, 0, 0), pygame.Rect(0, 0, 400, 400))
  for i in shotTiles:
    for j in i:
      j.draw()
  for i in hitTiles:
    for j in i:
      j.draw()
  pygame.draw.line(surf, (100, 100, 100), (0, 200), (200, 200), 3)
  renderText()
  pygame.display.flip()
def renderText():
  global font, text, surf
  words = text.split(" ")
  position = 0
  lineStart = True
  i = 0
  while i < len(words):
    words[i] += " "
    position += len(words[i]) - 1
    lineWasStarted = lineStart
    lineStart = False
    if position >= 14:
      position = len(words[i])
      if lineWasStarted:
        word = words[i]
        words[i] = word[0:15] + "\n"
        words.insert(i + 1, word[15:-1])
        i += 1
      else:
        words[i] = "\n" + words[i]
    lineWasStarted = False
    i += 1
  formattedText = ""
  for i in words:
    formattedText += i
  lines = formattedText.split("\n")
  line = 0
  for i in lines:
    finText = font.render(i, True, (255, 255, 255))
    rect = finText.get_rect()
    rect.x = 200
    rect.y = line * 20
    surf.blit(finText, rect)
    line += 1
def placeShip(name, length, positionsVariable):
  global hitTiles, shipPositions, text
  text = f"Click on {name} position 1"
  draw()
  pollClicks(2)
  while (lastClickPos[0], lastClickPos[1] - 10) in shipPositions:
    pollClicks(2)
  positionsVariable.append((lastClickPos[0], lastClickPos[1] - 10))
  shipPositions.append((lastClickPos[0], lastClickPos[1] - 10))
  hitTiles[lastClickPos[1] - 10][lastClickPos[0]].setType("S")
  draw()
  p1 = (lastClickPos[0], lastClickPos[1] - 10)
  direction = (0, 0)
  exceedsBoundaries = False
  text = f"Click on {name} position 2"
  draw()
  while bool(lastClickPos[0] == p1[0]) == bool(lastClickPos[1] - 10 == p1[1]) or exceedsBoundaries:
    exceedsBoundaries = False
    pollClicks(2)
    if lastClickPos[0] > p1[0]:
      direction = (1, 0)
    elif lastClickPos[0] < p1[0]:
      direction = (-1, 0)
    elif lastClickPos[1] - 10 > p1[1]:
      direction = (0, 1)
    elif lastClickPos[1] - 10 < p1[1]:
      direction = (0, -1)
    p2 = p1
    for i in range(length - 1):
      p2 = (p2[0] + direction[0], p2[1] + direction[1])
      if p2 in shipPositions:
        exceedsBoundaries = True
        break
      if p2[0] < 0 or p2[0] > 9 or p2[1] < 0 or p2[1] > 9:
        exceedsBoundaries = True
        break
  for i in range(length - 1):
    # Place the ship
    p1 = (p1[0] + direction[0], p1[1] + direction[1])
    positionsVariable.append(p1)
    shipPositions.append(p1)
    hitTiles[p1[1]][p1[0]].setType("S")
  draw()
def main():
  global shotTiles, hitTiles, shipPositions, aircraftCarrierPositions, battleshipPositions, cruiserPositions, submarinePositions, destroyerPositions, allPositions, surf, lastClickPos, prevClickPos, sinks, font, text
  pygame.init()
  atexit.register(pygame.quit)
  surf = pygame.display.set_mode((400, 400))
  font = pygame.font.Font(pygame.font.match_font("dejavusansmono"), 20)
  text = ""
  shotTiles = []
  hitTiles = []
  shipPositions = []
  shotPositions = []
  aircraftCarrierPositions = []
  battleshipPositions = []
  cruiserPositions = []
  submarinePositions = []
  destroyerPositions = []
  sinks = 0
  for y in range(0, 10):
    shotTiles.append([])
    hitTiles.append([])
    for x in range(0, 10):
      shotTiles[y].append(Tile(surf, x * 20, y * 20))
      hitTiles[y].append(Tile(surf, x * 20, y * 20 + 200))
  lastClickPos = None
  prevClickPos = None
  opponent = None
  allPositions = []
  for x in range(10):
    for y in range(10):
      allPositions.append((x, y))
  running = True
  firstIteration = True
  while running:
    for event in pygame.event.get():
      if event.type == QUIT:
        running = False
    draw()
    if firstIteration:
      firstIteration = False
      placeShip("aircraft carrier", 5, aircraftCarrierPositions)
      placeShip("battleship", 4, battleshipPositions)
      placeShip("cruiser", 3, cruiserPositions)
      placeShip("submarine", 3, submarinePositions)
      placeShip("destroyer", 2, destroyerPositions)
      opponent = Opponent()
    text = "Click to fire"
    draw()
    pollClicks(1)
    while lastClickPos in shotPositions:
      pollClicks(1)
    shotPositions.append(lastClickPos)
    if lastClickPos in opponent.aircraftCarrierPositions:
      if len(opponent.aircraftCarrierPositions) == 1:
        sinks += 1
        text = "You sank the computer's aircraft carrier!"
      else:
        text = "Hit!"
      shotTiles[lastClickPos[1]][lastClickPos[0]].setType("H")
      opponent.aircraftCarrierPositions.remove(lastClickPos)
    elif lastClickPos in opponent.battleshipPositions:
      if len(opponent.battleshipPositions) == 1:
        sinks += 1
        text = "You sank the computer's battleship!"
      else:
        text = "Hit!"
      shotTiles[lastClickPos[1]][lastClickPos[0]].setType("H")
      opponent.battleshipPositions.remove(lastClickPos)
    elif lastClickPos in opponent.cruiserPositions:
      if len(opponent.cruiserPositions) == 1:
        sinks += 1
        text = "You sank the computer's cruiser!"
      else:
        text = "Hit!"
      shotTiles[lastClickPos[1]][lastClickPos[0]].setType("H")
      opponent.cruiserPositions.remove(lastClickPos)
    elif lastClickPos in opponent.submarinePositions:
      if len(opponent.submarinePositions) == 1:
        sinks += 1
        text = "You sank the computer's submarine!"
      else:
        text = "Hit!"
      shotTiles[lastClickPos[1]][lastClickPos[0]].setType("H")
      opponent.submarinePositions.remove(lastClickPos)
    elif lastClickPos in opponent.destroyerPositions:
      if len(opponent.destroyerPositions) == 1:
        sinks += 1
        text = "You sank the computer's destroyer!"
      else:
        text = "Hit!"
      shotTiles[lastClickPos[1]][lastClickPos[0]].setType("H")
      opponent.destroyerPositions.remove(lastClickPos)
    else:
      text = "Miss"
      shotTiles[lastClickPos[1]][lastClickPos[0]].setType("M")
    draw()
    sleep(1)
    if sinks == 5:
      text = "You win!"
      draw()
      running = False
      break
    text = "Opponent is attacking..."
    draw()
    sleep(1)
    opponent.attack()
if __name__ == "__main__":
  main()