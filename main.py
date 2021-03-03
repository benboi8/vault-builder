import pygame as pg
from pygame import gfxdraw
import json
import cv2
import time
from PIL import Image

"""
TODO:
	finish interfaces; add info; add dwellers
	change demolish conditions; fix recursion to stop checks looping back on themselves
	add more rooms?;experiment specific rooms?
"""

# initialise pygame
pg.init()
clock = pg.time.Clock()

# scaling factor
# 1 = 640, 360
# 2 = 1280, 720
# 3 = 1920, 1080
SF = 2
WIDTH, HEIGHT = 640 * SF, 360 * SF
mainWindow = pg.display.set_mode((WIDTH, HEIGHT))
FPS = 60

# paths
roomImagePath = "assets/rooms/"
scaledRoomImagePath = "temp/assets/rooms/"
roomDataFilePath = "assets/roomData.json"

resourceImagePath = "assets/resources"
scaledResourceImagePath = "temp/assets/resources"
resourceDataFilePath = "assets/resourceData.json"


# colours
colBlack = (0, 0, 0)
colWhite = (255, 255, 255)
colLightGray = (205, 205, 205)
colDarkGray = (55, 55, 55)
colRed = (200, 0, 0)
colGreen = (0, 200, 0)
colBlue = (0, 0, 200)
colOrange = (255, 145, 0)
colLightGreen = (0, 255, 48)

roomColors = {
	"colWaterRoom": (195, 235, 250),
	"colFoodRoom": (255, 145, 0),
	"colPowerRoom": (255, 255, 100),
	"colLabRoom": (180, 180, 180),
	"colLoungeRoom": (75, 75, 200),
	"colAdminRoom": (77, 77, 77),
	"colLiftRoom": (130, 130, 130),
	"colVaultDoor": (110, 110, 110),
	"colRadioRoom": (115, 77, 25),
	"colTrainingRoom": (140, 140, 140),
	"colSecurityRoom": (80, 80, 80)
}

colMoneyResource = (133, 187, 101)

colCancel = (200, 140, 140)
colDemolish = (230, 110, 110)

# create font object
FONT = pg.font.SysFont("arial", 8 * SF)

# room info
# used to make building buttons
# order determines button order
# "name", "roomData name"
buildingButtonListData = [
("Lift", "lift"),
("Water", "water"),
("Food", "food"),
("Power", "power"),
("Lounge", "lounge"),
("Admin", "admin"),
("Lab", "lab"),
("Radio", "radio"),
("Training", "trainingRoom"),
("Security", "security")]
roomInfoLabels = []
roomWidth = 50
roomHeight = 50
numOfStartingRooms = 3

# pages
buildPageMin = 1
buildPageMax = 6
buildPageMaxUpgrade = 16

buildPageMin = min(1, buildPageMin)
buildPageMax = max(buildPageMin + 5, buildPageMax)
buildPage = buildPageMin
buildingPages = [[] for i in range(buildPageMin, buildPageMax)]
rowHeights = []

buildScrollMin = 1
buildScrollMax = len(buildingButtonListData)
buildScrollNum = buildScrollMin
buildScrollPages = []
columnWidths = []
scrollAmount = 40 * SF

# contains all objects
allButtons = []
allRooms = []
tempRooms = []
allLabels = []
allSliders = []
allResources = []
placementOptions = []

boundingRect = pg.Rect(50.5 * SF, 50.5 * SF, 550 * SF, 249 * SF)
scrollCollideingRect = pg.Rect(50 * SF, 310 * SF, 500 * SF, 30 * SF)

# determines what can be done in game e.g. building rooms
gameState = "NONE"
# primary button actions e.g. build button
allActions = ["BUILD", "SETTINGS"]
# used for secondary buttons
pressed = False
sliderMoving = (False, False)

loopFormedRecursionNum = 0


def DrawRectOutline(surface, color, rect, width=1):
	x, y, w, h = rect
	width = max(width, 1)  # Draw at least one rect.
	width = min(min(width, w//2), h//2)  # Don't overdraw.

	# This draws several smaller outlines inside the first outline
	# Invert the direction if it should grow outwards.
	for i in range(int(width)):
		pg.gfxdraw.rectangle(surface, (x+i, y+i, w-i*2, h-i*2), color)


def GetCenterOfRect(rect):
	x, y, w, h = rect
	midX, midY = (x + w) // 2, (y + h) // 2
	return midX, midY


def ResizeImage(imagePath, imageScale, newImagePath):
	image = Image.open(imagePath)
	image = image.resize((imageScale[0], imageScale[1]), Image.ANTIALIAS)
	image.save(newImagePath)


class ToggleButton:
	def __init__(self, surface, rect, buttonType, colorData, textData, actionData={}, lists=[allButtons]):
		self.surface = surface
		self.rect = pg.Rect(rect[0] * SF, rect[1] * SF, rect[2] * SF, rect[3] * SF)
		self.type = buttonType[0]
		self.action = buttonType[1]
		self.activeColor = colorData[0]
		self.inactiveColor = colorData[1]
		self.currentColor = self.inactiveColor
		self.text = textData[0]
		self.textColor = textData[1]
		self.active = False
		self.textSurface = FONT.render(self.text, True, self.textColor) 
		self.actionData = actionData
		for listToAppend in lists:
			listToAppend.append(self)

	def Draw(self):
		pg.draw.rect(self.surface, self.currentColor, self.rect)
		self.surface.blit(self.textSurface, self.rect)

	def HandleEvent(self, event):
		if event.type == pg.MOUSEBUTTONUP:
			if event.button == 1: # left mouse button
				if self.rect.collidepoint(pg.mouse.get_pos()):
					self.active = not self.active

		if self.active:
			self.currentColor = self.activeColor
		else:
			self.currentColor = self.inactiveColor


class HoldButton:
	def __init__(self, surface, rect, buttonType, colorData, textData, actionData={}, lists=[allButtons]):
		self.surface = surface
		self.rect = pg.Rect(rect[0] * SF, rect[1] * SF, rect[2] * SF, rect[3] * SF)
		self.type = buttonType[0] 
		self.action = buttonType[1]
		self.active = False
		self.activeColor = colorData[0]
		self.inactiveColor = colorData[1]
		self.currentColor = self.inactiveColor
		self.text = textData[0]
		self.textColor = textData[1]
		self.textSurface = FONT.render(self.text, True, self.textColor)
		self.actionData = actionData
		for listToAppend in lists:
			listToAppend.append(self)

	def Draw(self):
		pg.draw.rect(self.surface, self.currentColor, self.rect)
		self.surface.blit(self.textSurface, self.rect)

	def HandleEvent(self, event):
		if event.type == pg.MOUSEBUTTONDOWN:
			if event.button == 1:
				if self.rect.collidepoint(pg.mouse.get_pos()):
					self.active = True

		if event.type == pg.MOUSEBUTTONUP:
			if event.button == 1:
				self.active = False

		if self.active:
			self.currentColor = self.activeColor
		else:
			self.currentColor = self.inactiveColor


class Slider:
	def __init__(self, surface, rect, sliderType, colors, textData, bounds):
		self.surface = surface
		self.rect = pg.Rect(rect[0] * SF, rect[1] * SF, rect[2] * SF, rect[3] * SF)
		self.type = sliderType[0]
		self.action = sliderType[1]
		self.borderColor = colors[0]
		self.activeColor = colors[1]
		self.inactiveColor = colors[2]
		self.sliderColor = self.inactiveColor
		self.bounds = bounds
		self.text = textData[0]
		self.textColor = textData[1]
		self.value = round(self.bounds[0], 0)
		self.textSurface = FONT.render(self.text, True, self.textColor, self.sliderColor)
		self.active = False
		self.direction = "right"
		self.segmentLength = self.rect.w / self.bounds[1]
		self.sliderRect = pg.Rect(self.rect.x, self.rect.y, self.segmentLength, self.rect.h)
		allSliders.append(self)

	def Draw(self, width=3):
		DrawRectOutline(self.surface, self.borderColor, self.rect, width)
		self.DrawSlider()
		self.surface.blit(self.textSurface, ((self.sliderRect.x + self.sliderRect.w // 2) - self.textSurface.get_width() // 2, self.sliderRect.y))

	def DrawSlider(self):
		pg.draw.rect(self.surface, self.sliderColor, self.sliderRect)

	def HandleEvent(self, event):
		if event.type == pg.MOUSEBUTTONDOWN:
			if event.button == 1:
				mousePos = pg.mouse.get_pos()
				if self.rect.collidepoint(mousePos):
					self.sliderRect.x = mousePos[0] - self.sliderRect.w // 2
					self.active = True

		if event.type == pg.MOUSEBUTTONUP:
			if event.button == 1:
				self.active = False

		if self.active:
			self.sliderColor = self.activeColor
		else:
			self.sliderColor = self.inactiveColor

		self.MoveSlider()

	def MoveSlider(self):
		motion = pg.mouse.get_rel()
		if motion[0] <= 0:
			self.direction = "left"
		elif motion[0] > 0:
			self.direction = "right"

		if self.active:
			mousePosX = pg.mouse.get_pos()[0]
			if mousePosX < self.rect.x + self.rect.w - self.sliderRect.w // 2:
				if mousePosX > self.rect.x + self.sliderRect.w // 2:
					self.sliderRect.x = mousePosX - self.sliderRect.w // 2
					self.ChangeValue()
		self.textSurface = FONT.render(self.text, True, self.textColor, self.sliderColor)

	def ChangeValue(self):
		self.value = max(round(((self.sliderRect.x - self.rect.x) / self.rect.w) * (self.bounds[1] + 1), 0), self.bounds[0])

	def ChangeRect(self):
		self.sliderRect.x = self.value * self.segmentLength


class Label:
	def __init__(self, surface, rect, gameStateType, colors, textData, lists=[allLabels]):
		self.surface = surface
		self.rect = pg.Rect(rect[0] * SF, rect[1] * SF, rect[2] * SF, rect[3] * SF)
		self.gameStateType = gameStateType
		self.borderColor = colors[0]
		self.backgroundColor = colors[1]
		self.text = str(textData[0])
		self.textColor = textData[1]
		self.fontSize = textData[2]
		self.alignText = textData[3]
		self.font = pg.font.SysFont("arial", self.fontSize * SF)
		self.textSurface = self.font.render(self.text, True, self.textColor, self.backgroundColor)
		if self.alignText == "center-center":
			self.textRect = pg.Rect((self.rect[0] + self.rect[2] // 2) - self.textSurface.get_width() // 2, (self.rect[1] + self.rect[3] // 2) - self.textSurface.get_height() // 2, rect[2], rect[3])
		elif self.alignText == "top-center":
			self.textRect = pg.Rect((self.rect[0] + self.rect[2] // 2) - self.textSurface.get_width() // 2, self.rect[1] + 3 * SF, self.rect[2], self.rect[3])
		elif self.alignText == "top-left":
			self.textRext = self.rect
		else:
			self.textRext = self.rect

		for listToAppend in lists:
			listToAppend.append(self)

	def Draw(self):
		pg.draw.rect(mainWindow, self.backgroundColor, self.rect)
		self.surface.blit(self.textSurface, self.textRect)
		if self.borderColor != False:
			DrawRectOutline(mainWindow, self.borderColor, self.rect, 3 * SF)

	def UpdateText(self, text):
		self.textSurface = self.font.render(text, True, self.textColor, self.backgroundColor)
		self.textRect = pg.Rect((self.rect[0] + self.rect[2] // 2) - self.textSurface.get_width() // 2, (self.rect[1] + self.rect[3] // 2) - self.textSurface.get_height() // 2, self.rect[2], self.rect[3])


class Room:
	def __init__(self, surface, pos, dataFilePath, roomName):
		self.surface = surface
		with open(dataFilePath, "r") as roomDataFile:
			allRoomData = json.load(roomDataFile)
			roomData = allRoomData[roomName]

		self.rect = pg.Rect(pos[0] * SF, pos[1] * SF, roomWidth * roomData["dimensions"]["width"] * SF, roomHeight * roomData["dimensions"]["height"] * SF)
		self.color = roomData["drawData"]["color"]
		self.textColor = roomData["drawData"]["textColor"]
		self.name = roomData["name"] # display name
		self.resourceType = roomData["resource"]["type"]
		self.resourceAmount = roomData["resource"]["amount"]
		self.workPeriod = roomData["resource"]["time"]
		self.level = roomData["levelData"]["level"]
		self.maxLevel = roomData["levelData"]["maxLevel"]
		self.levelCostFunction = roomData["levelData"]["levelCostFunction"]
		self.joinedRooms = roomData["levelData"]["joinedRooms"]
		self.joinedRoomLevel = roomData["levelData"]["joinedRoomLevel"]
		self.dwellersWorking = roomData["dwellers"]

		self.selected = False

		image = roomData["drawData"]["image"]
		if not image:
			self.image = image
			self.hasImage = False
		else: 
			ResizeImage(roomImagePath + self.name + ".png", (self.rect.w, self.rect.h), scaledRoomImagePath + self.name + " up.png")
			self.image = pg.image.load(scaledRoomImagePath + self.name + " up.png")
			self.hasImage = True
		self.text = self.name
		self.textSurface = FONT.render(self.text, True, self.textColor)

	def Draw(self):
		if self.hasImage:
			self.surface.blit(self.image, self.rect)
		else:
			pg.draw.rect(self.surface, self.color, self.rect)
			self.surface.blit(self.textSurface, self.rect)

		if self.selected:
			DrawRectOutline(self.surface, colLightGreen, self.rect, 1.5 * SF)

	def UpdateRect(self, pos):
		x, y = pos
		self.rect = pg.Rect(x, y, self.rect.w, self.rect.h)


class Resource:
	def __init__(self, surface, rect, resourceName, resourceDataPath):
		self.surface = surface
		self.rect = pg.Rect(rect[0] * SF, rect[1] * SF, rect[2] * SF, rect[3] * SF)

		with open(resourceDataPath, "r") as resourceDataFile:
			allResourceData = json.load(resourceDataFile)
			self.resourceData = allResourceData[resourceName]

		self.name = self.resourceData["name"]
		self.roomType = self.resourceData["roomType"]
		self.startingValue = self.resourceData["value"]["startValue"]
		self.value = self.startingValue
		self.minAmount = self.resourceData["value"]["minimum"]
		self.maxAmount = self.resourceData["value"]["maximum"]
		self.color = self.resourceData["drawData"]["color"]
		self.textColor = self.resourceData["drawData"]["textColor"]
		image = self.resourceData["drawData"]["image"]

		if not image:
			self.image = image
			self.hasImage = False
		else: 
			ResizeImage(resourceImagePath + self.name + ".png", (self.rect.w, self.rect.h), scaledResourceImagePath + self.name + " up.png")
			self.image = pg.image.load(scaledRoomImagePath + self.name + " up.png")
			self.hasImage = True

		self.text = "{name}: {value}".format(name=self.name, value=self.value)
		self.textSurface = FONT.render(self.text, True, self.textColor)
		allResources.append(self)


	def Draw(self):
		if self.hasImage:
			self.surface.blit(self.image, self.rect)
		else:
			pg.draw.rect(self.surface, self.color, self.rect)
			self.surface.blit(self.textSurface, self.rect)

	def UpdateValue(self, newValue):
		self.value = newValue
		self.text = "{name}: {value}".format(name=self.name, value=self.value)
		self.textSurface = FONT.render(self.text, True, self.textColor)


def CreateResources():
	global waterResource, foodResource, powerResource, moneyResource
	waterResource = Resource(mainWindow, (200, 5, 50, 15), "water", resourceDataFilePath)
	foodResource = Resource(mainWindow, (260, 5, 50, 15), "food", resourceDataFilePath)
	powerResource = Resource(mainWindow, (320, 5, 50, 15), "power", resourceDataFilePath)
	moneyResource = Resource(mainWindow, (380, 5, 50, 15), "money", resourceDataFilePath)


def CreateButtons():
	global pageUpBuildButton, pageBuildNumber, pageDownBuildButton
	CreateBuildingButtons()
	width, height = 30, 30
	pageUpBuildButton = HoldButton(mainWindow, (605, (360 // 2) - 55, width, height), ("GAME", "BUILD PAGE UP"), (colWhite, colLightGray), ("Up", colDarkGray))
	pageBuildNumber = Label(mainWindow, (605, 360 // 2 - 15, width, height), "GAME", (colLightGray, colDarkGray), (buildPage, colLightGray, 24, "center-center"))
	pageDownBuildButton = HoldButton(mainWindow, (605 , (360 // 2) + 25, width, height), ("GAME", "BUILD PAGE DOWN"), (colWhite, colLightGray), ("Down", colDarkGray))


def CreateBuildingButtons():
	global cancelBuildButton, demolishBuildButton, buildButton, buildScrollSlider
	# building button
	startX, startY = 10, 310
	width, height = 30, 30
	buildButton = ToggleButton(mainWindow, (startX, startY, width, height), ("GAME", "BUILD"), (colWhite, colLightGray), ("Build", colDarkGray))
	x = startX
	for buttonData in buildingButtonListData:
		x += width + 5 * SF
		name = buttonData[0]
		actionData = buttonData[1]
		color = roomColors["col" + name + "Room"]
		roomButton = HoldButton(mainWindow, (x, startY, width, height), ("BUILD", "ADD ROOM"), (color, color), (name, colDarkGray), actionData) 
		buildScrollPages.append(roomButton)

	cancelBuildButton = HoldButton(mainWindow, (10, 230, width, height), ("BUILD", "INCREASE BUILD AREA"), (colGreen, colLightGreen), ("Expand", colDarkGray))
	cancelBuildButton = HoldButton(mainWindow, (10, 270, width, height), ("BUILD", "CANCEL"), (colRed, colCancel), ("Cancel", colDarkGray))
	demolishBuildButton = ToggleButton(mainWindow, (595, 315, width + 10, height + 10), ("BUILD", "DEMOLISH"), (colRed, colDemolish), ("Demolish", colDarkGray))

	buildScrollLeftButton = HoldButton(mainWindow, (40, 348, 10, 10), ("BUILD", "SCROLL LEFT"), (colWhite, colLightGray), (" <", colDarkGray))
	buildScrollRightButton = HoldButton(mainWindow, (580, 348, 10, 10), ("BUILD", "SCROLL RIGHT"), (colWhite, colLightGray), (" >", colDarkGray))
	buildScrollSlider = Slider(mainWindow, (50, 348, 530, 10), ("BUILD", "SCROLL"), (colLightGray, colWhite, colLightGray), (" ||| ", colDarkGray), (buildScrollMin, buildScrollMax))


def DrawLoop():
	global boundingRect
	mainWindow.fill(colDarkGray)

	DrawRectOutline(mainWindow, colLightGray, (boundingRect.x - 1.5 * SF, boundingRect.y - 1.5 * SF, boundingRect.w + 2 * SF, boundingRect.h + 3 * SF), 1 * SF)

	for label in allLabels:
		label.Draw()

	for label in roomInfoLabels:
		label.Draw()

	for button in allButtons:
		if button.type == "GAME":
			button.Draw()
		if gameState == "BUILD":
			if button.type == "BUILD":
				if button.action == "ADD ROOM":
					if button.rect.colliderect(scrollCollideingRect):
						button.Draw()
				else:
					button.Draw()

	for slider in allSliders:
		if slider.type == "GAME":
			slider.Draw()
		if gameState == "BUILD":
			if slider.type == "BUILD":
				slider.Draw()

	for resource in allResources:
		resource.Draw()


	if gameState == "BUILD":
		if len(tempRooms) > 0:
			for placementOption in placementOptions:
				DrawRectOutline(mainWindow, colOrange, placementOption, 4)

	DrawRooms()


	pg.display.update()


def DrawRooms():
	for page in buildingPages:
		for room in page:
			if boundingRect.colliderect(room.rect):
				room.Draw()


def GetBuildPageRowHeights():
	y = 50 * SF
	for i in range(buildPageMin, buildPageMax+1):
		rowHeights.append(y)
		y += roomHeight * SF


def GetBuildScrollColumnWidths():
	x = 50 * SF
	for i in range(buildScrollMin, buildScrollMax+1):
		columnWidths.append(x)
		x -= scrollAmount


def AddStartingRooms():
	# add starting rooms
	vaultDoor = Room(mainWindow, (50, 50), roomDataFilePath, "vaultDoor")
	allRooms.append(vaultDoor)
	buildingPages[0].append(vaultDoor)
	liftStartY = 50
	y = liftStartY
	for i in range(numOfStartingRooms-1):
		lift = Room(mainWindow, ((allRooms[0].rect.x + allRooms[0].rect.w) // SF, y), roomDataFilePath, "lift")
		y += liftStartY
		allRooms.append(lift)
		buildingPages[0].append(lift)


def PrimaryButtonPress(event):
	global gameState
	if event.type == pg.MOUSEBUTTONUP:
		if event.button == 1:
			for button in allButtons:
				if button.action in allActions:
					if button.active:
						gameState = button.action
					else:
						gameState = "NONE"


def SecondaryButtonPress(event):
	global pressed, sliderMoving
	infoLabelPressed = False
	if event.type == pg.MOUSEBUTTONDOWN:
		if event.button == 1:
			if not pressed:
				if gameState == "NONE":
					for room in allRooms:
						if room.rect.colliderect(boundingRect):
							if room.rect.collidepoint(pg.mouse.get_pos()):
								RoomClicked(room)
								pressed = True
								return
					for label in roomInfoLabels:
						if label.rect.collidepoint(pg.mouse.get_pos()):
							pressed = True
							infoLabelPressed = True
							if label in allButtons:
								if label.active:
									if label.action == "UPGRADE ROOM":
										UpgradeRoom(label)

						if not infoLabelPressed:
							RoomClicked(False)

				for button in allButtons:
					if button.active:
						if button.action == "BUILD PAGE DOWN":
							BuildPage("down")
						if button.action == "BUILD PAGE UP":
							BuildPage("up")

					if gameState == "BUILD":
						if button.active:
							if button.rect.colliderect(scrollCollideingRect):
								if button.action == "ADD ROOM" and not demolishBuildButton.active:
									pressed = True
									AddRoom(button.actionData)
							if button.action == "CANCEL":
								pressed = True
								CancelBuild()
							if button.action == "DEMOLISH":
								pressed = True
								CancelBuild()
								DemolishBuild()
							if button.action == "SCROLL RIGHT":
								pressed = True
								ScrollBuildMenu("right")
							if button.action == "SCROLL LEFT":
								pressed = True
								ScrollBuildMenu("left")
							if button.action == "INCREASE BUILD AREA":
								pressed = True
								IncreaseBuildArea()

				for slider in allSliders:
					if gameState == "BUILD":
						if slider.type == "BUILD":
							if slider.action == "SCROLL":
								if slider.active:
									sliderMoving = (True, slider)

	if event.type == pg.MOUSEBUTTONUP:
		if event.button == 1:
			pressed = False
			sliderMoving = (False, False)

	if sliderMoving[0]:
		ScrollBuildMenu(sliderMoving[1])


def IncreaseBuildArea():
	global buildPageMax
	# cost check
	if buildPageMax + 1 <= buildPageMaxUpgrade:
		buildPageMax += 1 


def RoomClicked(room):
	global roomInfoLabels
	roomInfoLabels = []
	for r in allRooms:
		r.selected = False			

	if room != False:
		roomNameLabel = Label(mainWindow, (50, 305, 540, 50), "NONE", (colLightGray, room.color), ("{name}: level: {lvl}".format(name=room.name, lvl=room.level), colBlack, 14, "top-center"), [roomInfoLabels])
		upgradeRoom = HoldButton(mainWindow, (60, 315, 30, 30), ("NONE", "UPGRADE ROOM") ,(colBlack, colDarkGray), ("Upgrade", colLightGray), {"room": room}, [roomInfoLabels, allButtons])
		room.selected = True


def UpgradeRoom(button):
	room = button.actionData["room"]
	maxLevel = room.maxLevel
	if room.level + 1 <= maxLevel:
		# add cost check
		room.level += 1
	button.actionData = {"room" : room}
	RoomClicked(room)


def CancelBuild():
	if len(tempRooms) > 0:
		tempRooms.pop()


def CheckAllConnections(room):
	leftRect = pg.Rect(room.rect.x - room.rect.w, room.rect.y, room.rect.w, room.rect.h)
	rightRect = pg.Rect(room.rect.x + room.rect.w, room.rect.y, room.rect.w, room.rect.h)
	upRect = pg.Rect(room.rect.x, room.rect.y - room.rect.h, room.rect.w, room.rect.h)
	downRect = pg.Rect(room.rect.x, room.rect.y + room.rect.h, room.rect.w, room.rect.h)
	leftRoom = None
	rightRoom = None
	upRoom = None
	downRoom = None
	leftRoom = leftRect.collidelist(allRooms)
	rightRoom = rightRect.collidelist(allRooms)
	upRoom = upRect.collidelist(allRooms)
	downRoom = downRect.collidelist(allRooms)

	return leftRoom, rightRoom, upRoom, downRoom


def CanRoomFormLoop(rooms, originalRoom):
	global loopFormedRecursionNum
	loopFormedRecursionNum += 1
	if loopFormedRecursionNum > 800:
		return
	loopFormed = False
	index = allRooms.index(originalRoom)

	leftIndex, rightIndex, upIndex, downIndex = CheckAllConnections(originalRoom)
	roomChecks = [False, False, False, False]
	if leftIndex != -1:
		roomChecks[0] = True
	if rightIndex != -1:
		roomChecks[1] = True
	if upIndex != -1:
		roomChecks[2] = True
	if downIndex != -1:
		roomChecks[3] = True

	if originalRoom.name == "Lift":
		numOfRooms = roomChecks.count(True)
		if (roomChecks[0] and roomChecks[1]) or (roomChecks[2] and roomChecks[3]):
			loopFormed = False
		elif roomChecks[2] and (not roomChecks[0] or not roomChecks[1]):
			loopFormed = True
		elif roomChecks[3] and (not roomChecks[0] or not roomChecks[1]):
			loopFormed = False
	else:
		if roomChecks[0] and roomChecks[1]:
			loopFormed = False
		else:
			loopFormed = True

	if loopFormed:
		loopFormed = False
		for page in buildingPages:
			if originalRoom in page:
				allRooms.remove(originalRoom)
				page.remove(originalRoom)


def DemolishBuild():
	for room in allRooms[numOfStartingRooms:]:
		if room.rect.collidepoint(pg.mouse.get_pos()):
			# checks if there is no room the left or right
			roomChecks = [False, False, False, False]
			leftIndex, rightIndex, upIndex, downIndex = CheckAllConnections(room)
			if leftIndex != -1:
				roomChecks[0] = True
			if rightIndex != -1:
				roomChecks[1] = True
			if upIndex != -1:
				roomChecks[2] = True
			if downIndex != -1:
				roomChecks[3] = True

			numOfRooms = roomChecks.count(True)
			if numOfRooms <= 1:
				allRooms.remove(room)
				for page in buildingPages:
					if room in page:
						page.remove(room)	
			else:
				CanRoomFormLoop([allRooms[allRooms.index(room) - 1]], room)
			

def AddRoom(roomName):
	if len(tempRooms) == 0:
		tempRooms.append(Room(mainWindow, (0, 0), roomDataFilePath, roomName))
		CalculatePossiblePlacements()


def MoveRoom(event):
	x, y = pg.mouse.get_pos()
	distancesX = []
	distancesY = []
	x, y = pg.mouse.get_pos()
	x -= tempRooms[0].rect.w / 2
	y -= tempRooms[0].rect.h / 2

	tempRooms[0].UpdateRect((x, y))

	CalculatePossiblePlacements()
	
	if event.type == pg.MOUSEBUTTONDOWN:
		if event.button == 1:
			CheckRoomPlacement()


def CheckRoomPlacement():
	global boundingRect
	# check money, check position and check total number of bulidings.
	room = tempRooms[0]

	# position check
	positionCheck = False
	if boundingRect.collidepoint(pg.mouse.get_pos()):
		positionCheck = True
	
	# overlap check
	overlapCheck = True
	for placedRoom in allRooms:
		if placedRoom.rect.collidepoint(pg.mouse.get_pos()):
			overlapCheck = False

	if overlapCheck and positionCheck:
		if len(placementOptions) > 0:
			for placementOption in placementOptions:
				if placementOption.collidepoint(pg.mouse.get_pos()):
					PlaceRoom(placementOption)
					return


def CalculatePossiblePlacements():
	global placementOptions
	placementOptions = []
	width, height = tempRooms[0].rect.w, tempRooms[0].rect.h
	boundX1, boundY1, boundX2, boundY2 = 49.5 * SF, 49.5 * SF, WIDTH - 25 * SF, HEIGHT - 49.5 * SF
	for room in allRooms:
		if boundingRect.colliderect(room.rect):
			validPlacement = False
			x, y, w, h = room.rect
			if tempRooms[0].name == "Lift" and room.name == "Lift":
				# check below the room
				x1 = x
				y1 = y + h
				rect = pg.Rect(x1, y1, width, height)
				if rect.y > boundY1:
					if rect.y + rect.h < boundY2:
						validPlacement = True
				if validPlacement:
					placementOptions.append(rect)
					validPlacement = False

				# check above the room
				x1 = x
				y1 = y - h
				rect = pg.Rect(x1, y1, width, height)
				if rect.y > boundY1:
					if rect.y + rect.h < boundY2:
							validPlacement = True
				if validPlacement:
					placementOptions.append(rect)
					validPlacement = False

			# check to the right of the room
			x1 = x + w
			y1 = y
			rect = pg.Rect(x1, y1, width, height)
			if rect.x > boundX1:
				if rect.x + rect.w < boundX2:
					if rect.collidelist(allRooms) == -1:
						validPlacement = True
			if validPlacement:
				placementOptions.append(rect)
				validPlacement = False

			# check to the left of the room
			x1 = x - width
			y1 = y
			rect = pg.Rect(x1, y1, width, height)
			if rect.x > boundX1:
				if rect.x + rect.w < boundX2:
					if rect.collidelist(allRooms) == -1:
						validPlacement = True
			if validPlacement:
				placementOptions.append(rect)
				validPlacement = False


def PlaceRoom(rect):
	global placementOptions
	room = tempRooms[0]
	room.rect = rect
	allRooms.append(room)
	tempRooms.pop()
	placementOptions = []
	index = rowHeights.index(room.rect.y)
	buildingPages[index].append(room)


def BuildPage(direction):
	global buildPage
	if direction == "down":
		if buildPage + 1 <= buildPageMax:
			buildPage += 1

			for page in buildingPages: 
				for room in page:
					room.rect.y -= room.rect.h

	if direction == "up":
		if buildPage - 1 >= buildPageMin:
			buildPage -= 1

			for page in buildingPages: 
				for room in page:
					room.rect.y += room.rect.h
	
	pageBuildNumber.UpdateText(str(buildPage))


def ScrollBuildMenu(direction):
	global buildScrollNum
	if direction == "left":
		if buildScrollNum - 1 >= buildScrollMin:
			buildScrollNum -= 1

			buildScrollSlider.value = buildScrollNum
			buildScrollSlider.ChangeRect()
			
			for button in buildScrollPages:
				button.rect.x += scrollAmount

	elif direction == "right":
		if buildScrollNum + 1 <= buildScrollMax:
			buildScrollNum += 1

			buildScrollSlider.value = buildScrollNum
			buildScrollSlider.ChangeRect()
			
			for button in buildScrollPages:
				button.rect.x -= scrollAmount

	else:
		slider = direction		
		value = int(slider.value)
		direction = slider.direction

		if buildScrollMin <= value <= buildScrollMax:
			buildScrollNum = value
			for button in buildScrollPages:
					button.rect.x = columnWidths[value - 1] + scrollAmount * buildScrollPages.index(button)


def HandleKeyboard(event):
	global gameState
	if event.type == pg.KEYDOWN:
		if event.key == pg.K_b:
			if gameState != "BUILD":
				gameState = "BUILD"
				buildButton.active = True
			else:
				gameState = "NONE"
				buildButton.active = False

		if gameState == "BUILD":
			if event.key == pg.K_LEFT:
				ScrollBuildMenu("left")
			if event.key == pg.K_RIGHT:
				ScrollBuildMenu("right")

	if event.type == pg.MOUSEBUTTONDOWN:
		if event.button == 4:
			BuildPage("up")
		if event.button == 5:
			BuildPage("down")

running = True
CreateButtons()
CreateResources()
AddStartingRooms()
GetBuildPageRowHeights()
GetBuildScrollColumnWidths()
DrawLoop()
while running:
	for event in pg.event.get():
		if event.type == pg.QUIT:
			running = False
		if event.type == pg.KEYDOWN:
			if event.key == pg.K_ESCAPE:
				running = False

		HandleKeyboard(event)

		if gameState == "BUILD":
			if len(tempRooms) > 0:
				MoveRoom(event)

		for button in allButtons:
			button.HandleEvent(event)

		for slider in allSliders:
			slider.HandleEvent(event)

		PrimaryButtonPress(event)
		SecondaryButtonPress(event)

	DrawLoop()