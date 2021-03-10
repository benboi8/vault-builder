import pygame as pg
from pygame import gfxdraw
import datetime as dt
import cv2
import json
from PIL import Image
import os
from os import listdir
from os.path import isfile, join

# initialise pygame
pg.init()
clock = pg.time.Clock()
running = True

# scaling factor
# 1 = 640, 360
# 2 = 1280, 720
# 3 = 1920, 1080
SF = 2
WIDTH, HEIGHT = 640 * SF, 360 * SF
mainWindow = pg.display.set_mode((WIDTH, HEIGHT), pg.DOUBLEBUF | pg.HWSURFACE | pg.SCALED, vsync=1)
FPS = 30

# paths
roomImagePath = "assets/rooms/"
tempRoomImagePath = "temp/assets/rooms/"
roomDataFilePath = "assets/roomData.json"

resourceImagePath = "assets/resources"
scaledResourceImagePath = "temp/assets/resources"
resourceDataFilePath = "assets/resourceData.json"

saveNum = 1
numOFSaveFiles = 6
savePath = "saves/"
saveRoomPath = "saves/Save {0}/roomData.json".format(saveNum)
loadRoomPath = "saves/Save {0}/roomData.json".format(saveNum)
saveGamePath = "saves/Save {0}/gameData.json".format(saveNum)
loadGamePath = "saves/Save {0}/gameData.json".format(saveNum)

buttonPath = "assets/buttons/"
tempButtonPath = "temp/assets/buttons/"

# colours
colBlack = (0, 0, 0)
colWhite = (255, 255, 255)
colLightGray = (205, 205, 205)
colDarkGray = (55, 55, 55)
colRed = (200, 0, 0)
colGreen = (0, 200, 0)
colBlue = (0, 0, 200)
colOrange = (255, 145, 0)
colLightRed = (255, 48, 0)
colLightGreen = (0, 255, 48)
colLightBlue = (48, 0, 255)

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
("Lounge", "lounge"),
("Water", "water"),
("Food", "food"),
("Power", "power"),
("Shop", "shop"),
("Admin", "admin"),
("Lab", "lab"),
("Radio", "radio"),
("Training", "trainingRoom"),
("Security", "security"),
]
roomInfoLabels = []
roomWidth = 50
roomHeight = 50
numOfStartingRooms = 3

# animaiton
roomOverlayAnimationCounter = 0
roomOverlayAnimationDuration = FPS * 2

roomAnimationCounter = 0
roomAnimationDuration = FPS

# settings button info
settingsButtonListData = [
("Save", "save", "SAVE"),
("Load", "load", "LOAD"),
("Exact", "exact", "EXACT"),
# ("640x360", "SF 1", "SF 1"),
# ("1280x720", "SF 2", "SF 2"),
# ("1920x1080", "SF 3", "SF 3"),
("Exit", "exit", "EXIT"),
]

# resource info
resourceList = [
"Water",
"Food",
"Power",
"Caps"
]

# pages
buildPageMin = 1
buildPageMax = 6
buildPageMinUpgrade = 6
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
allDwellers = []
allProgressBars = []
allLabels = []
allSliders = []
allResources = []
placementOptions = []
quitConfirmLabels = []
startMenuObjects = []
saveMenuObjects = []
loadMenuObjects = []

# demolish
demolishList = []

boundingRect = pg.Rect(50.5 * SF, 50.5 * SF, 550 * SF, 249 * SF)
scrollCollideingRect = pg.Rect(50 * SF, 310 * SF, 500 * SF, 30 * SF)

# determines what can be done in game e.g. building rooms
gameState = "START MENU"
# primary button actions e.g. build button
allActions = ["BUILD", "SETTINGS", "CONFIRM QUIT", "START MENU", "SAVE MENU", "LOAD MENU"]
buttonWidth, buttonHeight = 30, 30

increaseBuildAreaCost = 100
increaseBuildAreaMultiplier = 1.4

# used for secondary buttons
pressed = False
sliderMoving = (False, False)


def DrawRectOutline(surface, color, rect, width=1):
	x, y, w, h = rect
	width = max(width, 1)  # Draw at least one rect.
	width = min(min(width, w//2), h//2)  # Don't overdraw.

	# This draws several smaller outlines inside the first outline
	# Invert the direction if it should grow outwards.
	for i in range(int(width)):
		pg.gfxdraw.rectangle(surface, (x+i, y+i, w-i*2, h-i*2), color)


def DrawObround(surface, color, rect, filled=False, additive=True):
	x, y, w, h = rect

	radius = h // 2	
	# check if semicircles are added to the side or replace the side
	if not additive:
		x += radius
		w -= radius * 2
	# checks if it should be filled
	if not filled:
		pg.draw.aaline(surface, color, (x, y), (x + w, y), 3 * SF)
		pg.draw.aaline(surface, color, (x, y + h), (x + w, y + h), 3 * SF)
		pg.gfxdraw.arc(surface, x, y + radius, radius, 90, -90, color)
		pg.gfxdraw.arc(surface, x + w, y + radius, radius, -90, 90, color)
	else:
		pg.gfxdraw.filled_circle(surface, x, y + radius, radius, color)	
		pg.gfxdraw.filled_circle(surface, x + w, y + radius, radius, color)	
		pg.draw.rect(surface, color, (x, y, w, h))	


def GetCenterOfRect(rect):
	x, y, w, h = rect
	midX, midY = (x + w) // 2, (y + h) // 2
	return midX, midY


def ScaleImage(imagePath, imageScale, newImagePath):
	image = Image.open(imagePath)
	image = image.resize((imageScale[0], imageScale[1]))
	image.save(newImagePath)


def ChangeResolution(scalingFactor):
	global SF, WIDTH, HEIGHT, mainWindow, boundingRect, scrollCollideingRect, FONT

	SF = scalingFactor
	WIDTH, HEIGHT = 640 * SF, 360 * SF
	mainWindow = pg.display.set_mode((WIDTH, HEIGHT))

	FONT = pg.font.SysFont("arial", 8 * SF)

	for button in allButtons:
		button.Rescale()
	for slider in allSliders:
		slider.Rescale()
	for progressBar in allProgressBars:
		progressBar.Rescale()
	for label in allLabels:
		label.Rescale()
	for room in allRooms:
		room.Rescale()
	for resource in allResources:
		resource.Rescale()

	GetBuildPageRowHeights()
	GetBuildScrollColumnWidths()

	boundingRect = pg.Rect(50.5 * SF, 50.5 * SF, 550 * SF, 249 * SF)
	scrollCollideingRect = pg.Rect(50 * SF, 310 * SF, 500 * SF, 30 * SF)


class ToggleButton:
	def __init__(self, surface, rect, buttonType, colorData, textData, actionData=[], lists=[allButtons], extraText=[], imageData=[None]):
		"""
		Parameters: 
			buttonType: tuple of gameState type and button action
			colorData: tuple of active color and inactive color
			textData: tuple of text and text color
			actionData: list of any additional button action data
			lists: list of lists to add self too
			extraText: list of tuples containing the text and the rect
			imageData: list of image path and scaled image path
		"""
		self.surface = surface
		self.originalRect = rect
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
		self.extraTextSurfaces = []
		self.extraText = extraText

		for listToAppend in lists:
			listToAppend.append(self)

		self.imageData = imageData
		if self.imageData[0] != None:
			self.hasImage = True
		else:
			self.hasImage = False

		self.Rescale()

	# rescale all elements
	def Rescale(self):
		self.rect = pg.Rect(self.originalRect[0] * SF, self.originalRect[1] * SF, self.originalRect[2] * SF, self.originalRect[3] * SF)
		self.extraTextSurfaces = [] 
		for textData in self.extraText:
			textSurface = FONT.render(str(textData[0]), True, self.textColor)
			self.extraTextSurfaces.append((textSurface, ((textData[1][0] * SF) - textSurface.get_width() // 2, (textData[1][1] * SF) - textSurface.get_height() // 2)))

		if self.hasImage:
			ScaleImage(self.imageData[0], (self.rect.w, self.rect.h), self.imageData[1])
			self.image = pg.image.load(self.imageData[1])
			self.image.convert()

	def Draw(self):
		if not self.hasImage:
			pg.draw.rect(self.surface, self.currentColor, self.rect)
			self.surface.blit(self.textSurface, self.rect)
		else:
			self.surface.blit(self.image, self.rect)

		for textSurfaceData in self.extraTextSurfaces:
			self.surface.blit(textSurfaceData[0], textSurfaceData[1])

	def HandleEvent(self, event):
		# check for left mouse button down
		if event.type == pg.MOUSEBUTTONUP:
			if event.button == 1: # left mouse button
				if self.rect.collidepoint(pg.mouse.get_pos()):
					self.active = not self.active

		# change color
		if self.active:
			self.currentColor = self.activeColor
		else:
			self.currentColor = self.inactiveColor

	def ChangeRect(self, newRect):
		self.rect = pg.Rect(newRect)
		self.extraTextSurfaces = [] 
		for textData in self.extraText:
			textSurface = FONT.render(str(textData[0]), True, self.textColor)
			self.extraTextSurfaces.append((textSurface, ((self.rect.x + self.rect.w // 2) - textSurface.get_width() // 2, (self.rect.y + self.rect.h // 2) - textSurface.get_height() // 2)))


class HoldButton:
	def __init__(self, surface, rect, buttonType, colorData, textData, actionData=[], lists=[allButtons], extraText=[], imageData=[None]):
		"""
		Parameters: 
			buttonType: tuple of gameState type and button action
			colorData: tuple of active color and inactive color
			textData: tuple of text and text color
			actionData: list of any additional button action data
			lists: list of lists to add self too
			extraText: list of tuples containing the text and the rect
			imageData: list of image path and scaled image path
		"""
		self.surface = surface
		self.originalRect = rect
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
		self.extraText = extraText
		self.actionData = actionData
		for listToAppend in lists:
			listToAppend.append(self)
		
		self.imageData = imageData
		if self.imageData[0] != None:
			self.hasImage = True
		else:
			self.hasImage = False

		self.Rescale()

	# rescale all elements
	def Rescale(self):
		self.rect = pg.Rect(self.originalRect[0] * SF, self.originalRect[1] * SF, self.originalRect[2] * SF, self.originalRect[3] * SF)
		self.extraTextSurfaces = [] 
		for textData in self.extraText:
			textSurface = FONT.render(str(textData[0]), True, self.textColor)
			self.extraTextSurfaces.append((textSurface, ((textData[1][0] * SF) - textSurface.get_width() // 2, (textData[1][1] * SF) - textSurface.get_height() // 2)))
		if self.hasImage:
			ScaleImage(self.imageData[0], (self.rect.w, self.rect.h), self.imageData[1])
			self.image = pg.image.load(self.imageData[1])
			self.image.convert()

	def Draw(self):
		if not self.hasImage:
			pg.draw.rect(self.surface, self.currentColor, self.rect)
			self.surface.blit(self.textSurface, self.rect)
		else:
			self.surface.blit(self.image, self.rect)

		for textSurfaceData in self.extraTextSurfaces:
			self.surface.blit(textSurfaceData[0], textSurfaceData[1])

	def HandleEvent(self, event):
		# check for left mouse down
		if event.type == pg.MOUSEBUTTONDOWN:
			if event.button == 1:
				if self.rect.collidepoint(pg.mouse.get_pos()):
					self.active = True

		# check for left mouse up
		if event.type == pg.MOUSEBUTTONUP:
			if event.button == 1:
				self.active = False

		# change color
		if self.active:
			self.currentColor = self.activeColor
		else:
			self.currentColor = self.inactiveColor

	def ChangeRect(self, newRect):
		self.rect = pg.Rect(newRect)
		self.extraTextSurfaces = [] 
		for textData in self.extraText:
			textSurface = FONT.render(str(textData[0]), True, self.textColor)
			self.extraTextSurfaces.append((textSurface, ((self.rect.x + self.rect.w // 2) - textSurface.get_width() // 2, (self.rect.y + self.rect.h // 2) - textSurface.get_height() // 2)))

	def UpdateExtraText(self, extraText):
		self.extraTextSurfaces = []
		for textData in extraText:
			textSurface = FONT.render(str(textData[0]), True, self.textColor)
			self.extraTextSurfaces.append((textSurface, ((textData[1][0] * SF) - textSurface.get_width() // 2, (textData[1][1] * SF) - textSurface.get_height() // 2)))


class Slider:
	def __init__(self, surface, rect, sliderType, colors, textData, bounds, lists=[allSliders]):
		"""
		Parameters:
			sliderType: tuple of gameState type and slider action
			colors: tuple of active color and inactive color
			textData: tuple of text and text color and antialliasing
			bounds: tuple of lower bound and upper bound
			lists: list of lists to add self too
		"""
		self.surface = surface
		self.originalRect = rect
		self.type = sliderType[0]
		self.action = sliderType[1]
		self.borderColor = colors[0]
		self.activeColor = colors[1]
		self.inactiveColor = colors[2]
		self.sliderColor = self.inactiveColor
		self.bounds = bounds
		self.text = textData[0]
		self.textColor = textData[1]
		self.aa = textData[2]
		self.value = round(self.bounds[0], 0)
		self.active = False
		self.direction = "right"
		self.Rescale()
		for listToAppend in lists:
			listToAppend.append(self)

	# rescale all elements
	def Rescale(self):
		self.rect = pg.Rect(self.originalRect[0] * SF, self.originalRect[1] * SF, self.originalRect[2] * SF, self.originalRect[3] * SF)
		self.font = pg.font.SysFont("arial", self.aa * SF)
		self.textSurface = self.font.render(self.text, True, self.textColor)
		self.segmentLength = self.rect.w / self.bounds[1]
		self.sliderRect = pg.Rect(self.rect.x, self.rect.y, max(self.segmentLength, self.textSurface.get_width()), self.rect.h)
		self.collisionRect = pg.Rect(self.sliderRect.x - self.sliderRect.h // 2, self.sliderRect.y, self.sliderRect.w + self.sliderRect.h, self.sliderRect.h)
	
	def Draw(self, width=3):
		# draw outline
		DrawObround(self.surface, self.borderColor, self.rect)
		# draw slider
		DrawObround(self.surface, self.sliderColor, self.sliderRect, True)
		# draw text
		self.surface.blit(self.textSurface, ((self.sliderRect.x + self.sliderRect.w // 2) - self.textSurface.get_width() // 2, (self.sliderRect.y + self.sliderRect.h // 2) - self.textSurface.get_height() // 2))

	def HandleEvent(self, event):
		# check for left mouse button down
		if event.type == pg.MOUSEBUTTONDOWN:
			if event.button == 1:
				mousePos = pg.mouse.get_pos()
				if self.collisionRect.collidepoint(mousePos):
					self.active = True

		# check for left mouse button up
		if event.type == pg.MOUSEBUTTONUP:
			if event.button == 1:
				self.active = False

		# change color
		if self.active:
			self.sliderColor = self.activeColor
			self.MoveSlider()
		else:
			self.sliderColor = self.inactiveColor

	# change slider position
	def MoveSlider(self):
		# get slider direction
		motion = pg.mouse.get_rel()
		if motion[0] <= 0:
			self.direction = "left"
		elif motion[0] > 0:
			self.direction = "right"
	
		# set the slider x to mouse x
		mousePosX = pg.mouse.get_pos()[0]
		if mousePosX < self.rect.x + self.rect.w - self.sliderRect.w // 2:
			if mousePosX > self.rect.x + self.sliderRect.w // 2:
				self.sliderRect.x = mousePosX - self.sliderRect.w // 2
				self.ChangeValue()
		# update rect and text
		self.collisionRect = pg.Rect(self.sliderRect.x - self.sliderRect.h // 2, self.sliderRect.y, self.sliderRect.w + self.sliderRect.h, self.sliderRect.h)
		self.textSurface = FONT.render(self.text, True, self.textColor)

	def ChangeValue(self):
		self.value = max(round(((self.sliderRect.x - self.rect.x) / self.rect.w) * (self.bounds[1] + 1), 0), self.bounds[0])

	def ChangeRect(self):
		self.sliderRect.x = self.value * self.segmentLength


class ProgressBar:
	def __init__(self, surface, rect, percentageFilled, colorData, textData, drawData=[False, False], lists=[allProgressBars], extraData=[]):
		"""
		Parameters:
			colorData: tuple of color, background color
			textData: tuple of text, text color
			drawData: tuple of rounded edges and additive
			extraData: and additional data
		"""
		self.surface = surface
		self.originalRect = rect
		self.percentageFilled = percentageFilled
		self.color = colorData[0]
		self.backgroundColor = colorData[1]
		self.text = textData[0]
		self.textColor = textData[1]
		self.roundedEdges = drawData[0]
		self.additive = drawData[1]
		self.extraData = extraData

		self.Rescale()

		for listToAppend in lists:
			listToAppend.append(self)

	# rescale all elements
	def Rescale(self):
		self.rect = pg.Rect(self.originalRect[0] * SF, self.originalRect[1] * SF, self.originalRect[2] * SF, self.originalRect[3] * SF)

	def Draw(self):
		if self.roundedEdges:
			DrawObround(self.surface, self.color, self.rect, False, self.additive)
			DrawObround(self.surface, self.color, pg.Rect(self.rect.x, self.rect.y, self.rect.w * self.percentageFilled, self.rect.h), True, self.additive)
		else:
			DrawRectOutline(self.surface, self.color, self.rect)
			pg.draw.rect(self.surface, self.color, (self.rect.x, self.rect.y, self.rect.w * self.percentageFilled, self.rect.h))

	def Update(self, newPercentage):
		self.percentageFilled = newPercentage


class Label:
	def __init__(self, surface, rect, gameStateType, colors, textData, drawData=[False, False, True], lists=[allLabels], extraText=[]):
		"""
		Parameters:
			gameStateType: Which gameState to be drawn in
			colors: tuple of border color, background color
			textData: tuple of text, text color, font size, how to align text
			drawData: tuple of rounded edges, addititve, filled
			extraData: any additional data
		"""
		self.surface = surface
		self.originalRect = rect
		self.gameStateType = gameStateType
		self.borderColor = colors[0]
		self.backgroundColor = colors[1]
		self.text = str(textData[0])
		self.textColor = textData[1]
		self.fontSize = textData[2]
		self.alignText = textData[3]

		self.roundedEdges = drawData[0]
		self.additive = drawData[1]
		self.filled = drawData[2]

		self.extraText = extraText

		self.Rescale()

		for listToAppend in lists:
			listToAppend.append(self)

	# rescale all elements
	def Rescale(self):
		self.rect = pg.Rect(self.originalRect[0] * SF, self.originalRect[1] * SF, self.originalRect[2] * SF, self.originalRect[3] * SF)
		self.font = pg.font.SysFont("arial", self.fontSize * SF)
		self.textSurface = self.font.render(self.text, True, self.textColor)
		if self.alignText == "center-center":
			self.textRect = pg.Rect((self.rect[0] + self.rect[2] // 2) - self.textSurface.get_width() // 2, (self.rect[1] + self.rect[3] // 2) - self.textSurface.get_height() // 2, self.rect[2], self.rect[3])
		elif self.alignText == "top-center":
			self.textRect = pg.Rect((self.rect[0] + self.rect[2] // 2) - self.textSurface.get_width() // 2, self.rect[1] + 3 * SF, self.rect[2], self.rect[3])
		elif self.alignText == "top-left":
			self.textRext = self.rect
		else:
			self.textRext = self.rect

		self.extraTextSurfaces = []
		for textData in self.extraText:
			textSurface = FONT.render(str(textData[0]), True, self.textColor)
			x, y, w, h = (textData[1][0] * SF, textData[1][1] * SF, textData[1][2] * SF, textData[1][3] * SF)
			self.extraTextSurfaces.append((textSurface, (x - textSurface.get_width() // 2, y - textSurface.get_height() // 2, w, h)))

	def Draw(self):
		if self.roundedEdges:
			DrawObround(mainWindow, self.backgroundColor, self.rect, self.filled, self.additive)
			DrawObround(mainWindow, colDarkGray, (self.rect.x + 3, self.rect.y + 3, self.rect.w - 6, self.rect.h - 6), self.filled, self.additive)
		else:
			pg.draw.rect(mainWindow, self.backgroundColor, self.rect)
			if self.borderColor != False:
				DrawRectOutline(mainWindow, self.borderColor, self.rect, 3 * SF)
		self.surface.blit(self.textSurface, self.textRect)

		for textSurface in self.extraTextSurfaces:
			self.surface.blit(textSurface[0], textSurface[1])

	def UpdateText(self, text):
		self.textSurface = self.font.render(text, True, self.textColor)
		self.textRect = pg.Rect((self.rect[0] + self.rect[2] // 2) - self.textSurface.get_width() // 2, (self.rect[1] + self.rect[3] // 2) - self.textSurface.get_height() // 2, self.rect[2], self.rect[3])


class Room:
	def __init__(self, surface, pos, dataFilePath, roomName):
		self.surface = surface
		self.roomName = roomName
		self.pos = pos
		with open(dataFilePath, "r") as roomDataFile:
			allRoomData = json.load(roomDataFile)
			roomData = allRoomData[roomName]
			self.roomData = roomData

		self.color = roomData["drawData"]["color"]
		self.textColor = roomData["drawData"]["textColor"]
		self.name = roomData["name"] # display name
		self.resourceType = roomData["resource"]["type"]
		self.resourceAmount = roomData["resource"]["amount"]
		self.workTime = roomData["resource"]["time"]
		self.level = roomData["levelData"]["level"]
		self.multiplier = roomData["levelData"]["multiplier"]
		self.maxLevel = roomData["levelData"]["maxLevel"]
		self.baseCost = roomData["levelData"]["baseCost"]
		self.joinedRooms = roomData["levelData"]["joinedRooms"]
		self.joinedRoomMax = roomData["levelData"]["maxJoinedRooms"]
		self.dwellersWorking = roomData["dwellers"]
		self.joinedRooms.append(self)

		self.selected = False
		self.showingInfo = False
		self.resource = None
		for resource in allResources:
			if self.resourceType == resource.roomType:
				self.resource = resource

		self.text = self.name
		self.textSurface = FONT.render(self.text, True, self.textColor)

		self.seconds = []
		self.counter = 0
		self.numOfJoinedRooms = 0

		self.numOfFramesOverlay = 2
		self.overlayAnimation = []
		self.currentFrameOverlay = 0

		self.numOfFrames = 4
		self.animation = []
		self.currentFrame = 0

		self.resourcesAvaiable = False
		self.resource = None
		self.amountSpent = 0
		for resource in allResources:
			if resource.roomType == self.resourceType:
				self.resource = resource

		self.Rescale()
		self.CalculateCosts()

	def Rescale(self):
		self.width, self.height = roomWidth * self.roomData["dimensions"]["width"] * SF, roomHeight * self.roomData["dimensions"]["height"] * SF
		self.rect = pg.Rect(self.pos[0] * SF, self.pos[1] * SF, self.width, self.height)

		imagePath = self.roomData["drawData"]["image"]
		if imagePath != False:
			imagePath = self.roomData["drawData"]["image"]
			ScaleImage(roomImagePath + imagePath, (self.rect.w, self.rect.h * self.numOfFrames), tempRoomImagePath + imagePath)
			imageSurface = pg.image.load(tempRoomImagePath + imagePath)
			self.hasImage = True
			for i in range(self.numOfFrames):
				imageSubsurface = imageSurface.subsurface(pg.Rect(0, 0 + (i * self.rect.h), self.rect.w, self.rect.h))
				self.animation.append(imageSubsurface)
		else:
			self.hasImage = False

		imagePath = "GAME/RESOURCE COLLECTION OVERLAY animated.png"
		ScaleImage(buttonPath + imagePath, (self.rect.w, self.rect.h * self.numOfFramesOverlay), tempButtonPath + imagePath)
		imageSurface = pg.image.load(tempButtonPath + imagePath)
		for i in range(self.numOfFramesOverlay):
			imageSubsurface = imageSurface.subsurface(pg.Rect(0, 0 + (i * self.rect.h), self.rect.w, self.rect.h))
			self.overlayAnimation.append(imageSubsurface)

	def CalculateCosts(self):
		self.cost = self.baseCost
		self.UpdateCost()

	def Upgrade(self):
		if self.level + 1 <= self.maxLevel:
			self.level += 1
			self.UpdateCost()

	def UpdateCost(self):
		otherJoinedRooms = []
		for joinedRoom in self.joinedRooms:
			otherJoinedRooms.append(len(joinedRoom.joinedRooms))
			self.numOfJoinedRooms = max(1, max(otherJoinedRooms))
			if self.numOfJoinedRooms > len(self.joinedRooms):
				self.joinedRooms = joinedRoom.joinedRooms

		self.upgradeCost = round(self.level ** self.multiplier * self.baseCost) * max(1, self.numOfJoinedRooms)
	
	def Draw(self):
		# draw room 
		if self.hasImage:
			self.DrawAnimation()
		else:
			pg.draw.rect(self.surface, self.color, self.rect)
			# draw name
			self.surface.blit(self.textSurface, self.rect)

		if self.selected:
			DrawRectOutline(self.surface, colLightGreen, self.rect, 1.5 * SF)

		if self.resourcesAvaiable:
			self.DrawOverlay()

	def DrawAnimation(self):
		self.currentFrame = (round((roomAnimationCounter) / self.numOfFrames) % self.numOfFrames)
		
		self.surface.blit(self.animation[self.currentFrame], self.rect)

	def DrawOverlay(self):
		if roomOverlayAnimationCounter <= roomOverlayAnimationDuration / self.numOfFramesOverlay:
			self.currentFrameOverlay = 0
		else:
			self.currentFrameOverlay = 1
		self.surface.blit(self.overlayAnimation[self.currentFrameOverlay], self.rect)

	def DrawJoined(self):
		if len(self.joinedRooms) > 1:
			for joinedRoom in self.joinedRooms:
				pg.draw.aaline(self.surface, colBlack, (self.rect.x + self.rect.w // 2, self.rect.y + self.rect.h // 2), (joinedRoom.rect.x + joinedRoom.rect.w // 2, joinedRoom.rect.y + joinedRoom.rect.h // 2))

	def UpdateRect(self, pos):
		x, y = pos
		self.rect = pg.Rect(x, y, self.rect.w, self.rect.h)

	def Timer(self):
		if not self.resourcesAvaiable:
			second = dt.datetime.utcnow().second
			if second not in self.seconds:
				self.seconds.append(second)
				self.counter += 1

			if len(self.seconds) >= min(60, self.workTime):
				self.seconds = []

			if self.counter >= self.workTime:
				self.seconds = []
				self.resourcesAvaiable = True

	def AddResource(self):
		if self.resource != None:
			if self.resource.value + self.resourceAmount <= self.resource.maxAmount:
				self.resource.value += round((self.resourceAmount * self.level) * (1.08 * self.numOfJoinedRooms))
			else:
				self.resource.value = self.resource.maxAmount
			self.resource.UpdateRect()

	def CollectResources(self):
		self.resourcesAvaiable = False
		self.counter = 0
		self.AddResource()


class Resource:
	def __init__(self, surface, rect, resourceName, resourceDataPath):
		self.surface = surface
		self.originalRect = rect

		with open(resourceDataPath, "r") as resourceDataFile:
			allResourceData = json.load(resourceDataFile)
			self.resourceData = allResourceData[resourceName]

		self.name = self.resourceData["name"]
		self.roomType = self.resourceData["roomType"]
		self.startingValue = self.resourceData["value"]["startValue"]
		self.value = self.startingValue
		self.minAmount = self.resourceData["value"]["minimum"]
		self.maxAmount = self.resourceData["value"]["maximum"]
		self.valuePerMin = self.resourceData["value"]["valuePerMin"]
		self.usage = self.resourceData["value"]["usage"]
		self.workTime = self.resourceData["value"]["workTime"]
		self.color = self.resourceData["drawData"]["color"]
		self.drawFilled = self.resourceData["drawData"]["filled"]
		self.textColor = self.color
		if self.drawFilled:
			self.text = "{name}".format(name=self.name)
		else:
			value = int(self.value)
			self.text = "{name}: {value:,}".format(name=self.name, value=value)
		self.textSurface = FONT.render(self.text, True, self.textColor)
		self.exactAmounts = False
		self.seconds = []
		self.activeRooms = 0
		self.percentageFilled = self.value / (self.maxAmount - self.minAmount) 	
		self.counter = 0
		self.Rescale()
		allResources.append(self)

	def Rescale(self):
		self.rect = pg.Rect(self.originalRect[0] * SF, self.originalRect[1] * SF, self.originalRect[2] * SF, self.originalRect[3] * SF)
		self.filledRect = self.rect
		self.UpdateRect()

	def Draw(self):
		# draw outline
		if self.exactAmounts:
			value = int(self.value)
			self.text = "{name}: {value:,}".format(name=self.name, value=value)
		else:
			if self.drawFilled:
				self.text = "{name}".format(name=self.name)
			else:
				value = int(self.value)
				self.text = "{name}: {value:,}".format(name=self.name, value=value)

		self.textSurface = FONT.render(self.text, True, self.textColor)


		DrawObround(self.surface, self.color, self.rect)
		if self.drawFilled:
			# draw filled amount
			self.DrawAmount()
			self.surface.blit(self.textSurface, (self.rect.x + self.rect.w // 2- self.textSurface.get_width() // 2, (self.rect.y - self.rect.h // 2) - 2.5 * SF))
		else:
			# draw text
			self.surface.blit(self.textSurface, (self.rect.x + self.rect.w // 2- self.textSurface.get_width() // 2, self.rect.y + self.rect.h // 2 - self.textSurface.get_height() // 2))

	def DrawAmount(self):
		DrawObround(self.surface, self.color, self.filledRect, True)
		if self.filledRect.w <= 0:		
			pg.draw.rect(self.surface, colDarkGray, (self.rect.x, self.rect.y + 1, self.rect.w, self.rect.h - 1))

	def UpdateRect(self):
		self.filledRect = pg.Rect(self.rect.x, self.rect.y, self.rect.w, self.rect.h)
		self.percentageFilled = self.value / (self.maxAmount - self.minAmount) 
		self.filledRect.w *= self.percentageFilled

	def UpdateValue(self, newValue):
		if self.value + newValue <= self.maxAmount:
			if self.value + newValue >= self.minAmount:
				self.value += newValue
			else:
				self.value = self.minAmount
		else:
			self.value = self.maxAmount

		if self.drawFilled:
			self.text = "{name}".format(name=self.name)
		else:
			value = int(self.value)
			self.text = "{name}: {value:,}".format(name=self.name, value=value)

		self.textSurface = FONT.render(self.text, True, self.textColor)
		self.UpdateRect()

	def CalculateTime(self):
		second = dt.datetime.utcnow().second
		if second not in self.seconds:
			self.seconds.append(second)
			self.counter += 1

		if len(self.seconds) >= min(60, self.workTime):
			self.seconds = []

		if self.counter >= self.workTime:
			self.counter = 0
			self.seconds = []
			self.MinusResource()
			if self.drawFilled:
				self.text = "{name}".format(name=self.name)
			else:
				value = int(self.value)
				self.text = "{name}: {value:,}".format(name=self.name, value=value)

			self.textSurface = FONT.render(self.text, True, self.textColor)
			self.UpdateRect()

	def MinusResource(self):
		if self.value - max(self.usage, self.usage * len(allDwellers)) >= self.minAmount:
			self.value -= max(self.usage, self.usage * len(allDwellers))
		else:
			self.value = self.minAmount


def CreateResources():
	x, y, w, h = 200, 10, 40, 15
	for resource in resourceList:
		resource = Resource(mainWindow, (x, y, w, h), resource, resourceDataFilePath)
		x += 60


def CreateButtons():
	global pageUpBuildButton, pageBuildNumber, pageDownBuildButton
	CreateBuildingButtons()
	CreateSettingsButtons()
	pageUpBuildButton = HoldButton(mainWindow, (605, (360 // 2) - 55, buttonWidth, buttonHeight), ("GAME", "BUILD PAGE UP"), (colWhite, colLightGray), ("Up", colDarkGray), imageData=[buttonPath + "GAME/UP.png", tempButtonPath + "GAME/UP.png"])
	pageBuildNumber = Label(mainWindow, (605, 360 // 2 - 15, buttonWidth, buttonHeight), "GAME", (colLightGray, colDarkGray), (buildPage, colLightGray, 24, "center-center"))
	pageDownBuildButton = HoldButton(mainWindow, (605 , (360 // 2) + 25, buttonWidth, buttonHeight), ("GAME", "BUILD PAGE DOWN"), (colWhite, colLightGray), ("Down", colDarkGray), imageData=[buttonPath + "GAME/DOWN.png", tempButtonPath + "GAME/DOWN.png"])


def CreateBuildingButtons():
	global cancelBuildButton, demolishBuildButton, buildButton, buildScrollSlider
	# building button
	startX, startY = 10, 310
	buildButton = ToggleButton(mainWindow, (startX, startY, buttonWidth, buttonHeight), ("GAME", "BUILD"), (colWhite, colLightGray), ("Build", colDarkGray), imageData=[buttonPath + "GAME/build.png", tempButtonPath + "GAME/bulid.png"])
	x = startX
	for buttonData in buildingButtonListData:
		x += buttonWidth + 5 * SF
		name = buttonData[0]
		actionData = buttonData[1]
		rect = pg.Rect(x, startY, buttonWidth, buttonHeight)
		with open(roomDataFilePath, "r") as roomDataFile:
			roomData = json.load(roomDataFile)
			cost = roomData[actionData]["levelData"]["baseCost"]
			color = roomData[actionData]["drawData"]["color"]
		roomButton = HoldButton(mainWindow, rect, ("BUILD", "ADD ROOM"), (color, color), (name, colBlack), actionData, [allButtons], [(cost, pg.Rect(rect.x + rect.w // 2, rect.y +  rect.h // 2, rect.w, rect.h))]) 
		buildScrollPages.append(roomButton)

	decreaseBuildArea = HoldButton(mainWindow, (10, 190, buttonWidth, buttonHeight), ("BUILD", "DECREASE BUILD AREA"), (colRed, colLightRed), ("Shrink", colBlack), imageData=[buttonPath + "BUILD/shrink.png", tempButtonPath + "BUILD/shrink.png"])
	increaseBuildArea = HoldButton(mainWindow, (10, 230, buttonWidth, buttonHeight), ("BUILD", "INCREASE BUILD AREA"), (colGreen, colLightGreen), ("Expand", colBlack), imageData=[buttonPath + "BUILD/expand.png", tempButtonPath + "BUILD/expand.png"], extraText=[(str(increaseBuildAreaCost), (10 + buttonWidth // 2, 230 + buttonHeight // 2, buttonWidth, buttonHeight))])
	cancelBuildButton = HoldButton(mainWindow, (10, 270, buttonWidth, buttonHeight), ("BUILD", "CANCEL"), (colRed, colCancel), ("Cancel", colDarkGray), imageData=[buttonPath + "BUILD/cancel.png", tempButtonPath + "BUILD/cancel.png"])
	demolishBuildButton = ToggleButton(mainWindow, (595, 315, buttonWidth + 10, buttonHeight + 10), ("BUILD", "DEMOLISH"), (colRed, colDemolish), ("Demolish", colDarkGray), imageData=[buttonPath + "BUILD/demolish.png", tempButtonPath + "BUILD/demolish.png"])

	buildScrollSlider = Slider(mainWindow, (50, 348, 530, 10), ("BUILD", "SCROLL"), (colLightGray, colWhite, colLightGray), (" ||| ", colDarkGray, 8), (buildScrollMin, buildScrollMax))


def CreateSettingsButtons():
	startX, startY = 10, 10
	settingsButton = ToggleButton(mainWindow, (startX, startY, buttonWidth, buttonHeight), ("GAME", "SETTINGS"), (colWhite, colLightGray), ("Settings", colDarkGray), imageData=[buttonPath + "GAME/settings.png", tempButtonPath + "GAME/settings.png"])
	y = startY
	for buttonData in settingsButtonListData:
		y += buttonHeight + 5 * SF
		name = buttonData[0]
		actionData = buttonData[1]
		buttonAction = buttonData[2]
		color = (colWhite, colLightGray)
		settingsButton = HoldButton(mainWindow, (startX, y, buttonWidth, buttonHeight), ("SETTINGS", buttonAction), color, (name, colDarkGray), actionData, imageData=[buttonPath + "SETTINGS/" + buttonAction + ".png", tempButtonPath + "SETTINGS/" + buttonAction + ".png"])


def CreateStartMenuObjects():
	global startMenuObjects
	startMenuObjects = []
	title = Label(mainWindow, (40, 20, 560, 60), "START MENU", (colLightGray, colLightGray), ["Vault builder", colLightGray, 16, "center-center"], [True, True, False], [startMenuObjects])
	startNewSave = HoldButton(mainWindow, (230, 110, 200, 50), ("START MENU", "SAVE MENU"), (colLightGray, colLightGray), ("Start new save game.", colDarkGray), lists=[allButtons, startMenuObjects], imageData=[buttonPath + "START MENU/NEW SAVE.png", tempButtonPath + "START MENU/NEW SAVE.png"])
	loadSave = HoldButton(mainWindow, (230, 190, 200, 50), ("START MENU", "LOAD MENU"), (colLightGray, colLightGray), ("Load previous save.", colDarkGray), lists=[allButtons, startMenuObjects], imageData=[buttonPath + "START MENU/LOAD SAVE.png", tempButtonPath + "START MENU/LOAD SAVE.png"])
	exit = HoldButton(mainWindow, (230, 270, 200, 50), ("START MENU", "QUIT"), (colLightGray, colLightGray), ("Quit.", colDarkGray), lists=[allButtons, startMenuObjects], imageData=[buttonPath + "START MENU/QUIT.png", tempButtonPath + "START MENU/QUIT.png"])


def CreateSaveMenuObjects():
	global saveMenuObjects, saveMenuButtonCollisionRect
	saveMenuObjects = [[], []]
	title = Label(mainWindow, (40, 20, 560, 60), "SAVE MENU", (colLightGray, colLightGray), ["Please choose a save game.", colLightGray, 16, "center-center"], [True, True, False], [saveMenuObjects[0]])
	backButton = HoldButton(mainWindow, (230, 300, 200, 50), ("SAVE MENU", "BACK"), (colLightGray, colLightGray), ("Back", colDarkGray), lists=[allButtons, saveMenuObjects[1]])
	x, y, w, h = 230, 85, 200, 50
	numOfCollumns = 1
	saveMenuButtonCollisionRect = pg.Rect((x - 1) * SF, y * SF, 202 * SF,  300 * SF)
	for i in range(1, numOFSaveFiles+1):
		save = HoldButton(mainWindow, (x, y, w, h), ("SAVE MENU", "SAVE {0}".format(i)), (colLightGray, colLightGray), ("Save {0}".format(i), colDarkGray), lists=[allButtons, saveMenuObjects[1]])
		y += h + 10
		if y > 250:
			y = 85
			x += w + 10
			numOfCollumns += 1


def ScrollSaveMenu(direction):
	scrollLeft, scrollRight = False, True
	for button in saveMenuObjects[1]:
		if button in allButtons:
			scrollAmount = button.rect.w + (10 * 2)
			if button.action != "BACK":
				if direction == "left":
					# index starts at one to avoid the back button
					firstObj = saveMenuObjects[1][1]
					if firstObj.rect.x < saveMenuButtonCollisionRect.x:
						scrollLeft = True
							
					if scrollLeft:
						button.rect.x += scrollAmount

				if direction == "right":
					lastObj = saveMenuObjects[1][-1]
					if lastObj.rect.x - scrollAmount <= saveMenuButtonCollisionRect.x:
						scrollRight = False
						
					if scrollRight:
						button.rect.x -= scrollAmount


def CreateLoadMenuObjects():
	global loadMenuObjects, loadMenuButtonCollisionRect
	loadMenuObjects = [[], []]
	title = Label(mainWindow, (40, 20, 560, 60), "LOAD MENU", (colLightGray, colLightGray), ["Please choose a save game.", colLightGray, 16, "center-center"], [True, True, False], [loadMenuObjects[0]])
	backButton = HoldButton(mainWindow, (230, 300, 200, 50), ("LOAD MENU", "BACK"), (colLightGray, colLightGray), ("Back", colDarkGray), lists=[allButtons, loadMenuObjects[1]])
	x, y, w, h = 230, 85, 200, 50
	loadMenuButtonCollisionRect = pg.Rect((x - 1) * SF, y * SF, 202 * SF,  300 * SF)
	for i in range(1, numOFSaveFiles+1):
		load = HoldButton(mainWindow, (x, y, w, h), ("LOAD MENU", "LOAD {0}".format(i)), (colLightGray, colLightGray), ("Load {0}".format(i), colDarkGray), lists=[allButtons, loadMenuObjects[1]])
		y += h + 10
		if y > 250:
			y = 85
			x += w + 10
	

def ScrollLoadMenu(direction):
	scrollLeft, scrollRight = False, True
	for button in loadMenuObjects[1]:
		if button in allButtons:
			scrollAmount = button.rect.w + (10 * 2)
			if button.action != "BACK":
				if direction == "left":
					# index starts at one to avoid the back button
					firstObj = loadMenuObjects[1][1]
					if firstObj.rect.x < loadMenuButtonCollisionRect.x:
						scrollLeft = True
							
					if scrollLeft:
						button.rect.x += scrollAmount

				if direction == "right":
					lastObj = loadMenuObjects[1][-1]
					if lastObj.rect.x - scrollAmount <= loadMenuButtonCollisionRect.x:
						scrollRight = False
						
					if scrollRight:
						button.rect.x -= scrollAmount


def DrawLoop():
	global boundingRect
	mainWindow.fill(colDarkGray)

	if demolishBuildButton.active:
		DrawRectOutline(mainWindow, colRed, (boundingRect.x - 1.5 * SF, boundingRect.y - 1.5 * SF, boundingRect.w + 2 * SF, boundingRect.h + 3 * SF), 1 * SF)
	else:
		DrawRectOutline(mainWindow, colLightGray, (boundingRect.x - 1.5 * SF, boundingRect.y - 1.5 * SF, boundingRect.w + 2 * SF, boundingRect.h + 3 * SF), 1 * SF)

	for label in allLabels:
		label.Draw()

	for obj in roomInfoLabels:
		obj.Draw()
		if obj in allProgressBars:
			obj.Update(obj.extraData[0].counter / obj.extraData[0].workTime)

	for progressBar in allProgressBars:
		if progressBar not in roomInfoLabels: 
			progressBar.Draw()

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

		if gameState == "SETTINGS":
			if button.type == "SETTINGS":
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

	if gameState == "CONFIRM QUIT":
		DrawConfirmQuit()

	pg.display.update()


def DrawRooms():
	for page in buildingPages:
		for room in page:
			if boundingRect.colliderect(room.rect):
				room.Draw()

	for room in allRooms:
		if boundingRect.colliderect(room.rect):
			room.DrawJoined()


def DrawStartMenu():
	mainWindow.fill(colDarkGray)

	if gameState == "START MENU":
		for obj in startMenuObjects:
			obj.Draw()
	if gameState == "CONFIRM QUIT":
		DrawConfirmQuit()
	if gameState == "SAVE MENU":
		DrawSaveMenu()
	if gameState == "LOAD MENU":
		DrawLoadMenu()

	pg.display.update()


def DrawConfirmQuit():
	for label in quitConfirmLabels:
		label.Draw()


def DrawSaveMenu():
	for label in saveMenuObjects[0]:
		label.Draw()

	for button in saveMenuObjects[1]:
		if button.rect.colliderect(saveMenuButtonCollisionRect):
			button.Draw()	


def DrawLoadMenu():
	for label in loadMenuObjects[0]:
		label.Draw()

	for button in loadMenuObjects[1]:
		if button.rect.colliderect(loadMenuButtonCollisionRect):
			button.Draw()	


def GetBuildPageRowHeights():
	global rowHeights
	rowHeights = []
	y = 50 * SF
	for i in range(buildPageMin, buildPageMax+1):
		rowHeights.append(y)
		y += roomHeight * SF


def GetBuildScrollColumnWidths():
	global columnWidths
	columnWidths = []
	x = 50 * SF
	for i in range(buildScrollMin, buildScrollMax+1):
		columnWidths.append(x)
		x -= scrollAmount


def AddStartingRooms():
	# add starting rooms
	global buildingPages 
	buildingPages = [[] for i in range(buildPageMin, buildPageMax)]
	vaultDoor = Room(mainWindow, (50, 50), roomDataFilePath, "vaultDoor")
	allRooms.append(vaultDoor)
	buildingPages[0].append(vaultDoor)
	liftStartY = 50
	y = liftStartY
	for i in range(numOfStartingRooms-1):
		lift = Room(mainWindow, ((allRooms[0].rect.x + allRooms[0].rect.w) // SF, y), roomDataFilePath, "lift")
		y += liftStartY
		allRooms.append(lift)
		buildingPages[i].append(lift)


def HasRoomBeenClicked():
	global pressed, roomInfoLabels
	infoLabelPressed = False
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
					if label.action == "ROOM INFO":
						ShowRoomInfo(label)

		if not infoLabelPressed:
			for obj in roomInfoLabels:
				if obj in allProgressBars:
					allProgressBars.remove(obj)
			roomInfoLabels = []
			RoomClicked(False)


def BuildClick(button):
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
			IncreaseBuildArea(button)		
		if button.action == "DECREASE BUILD AREA":
			pressed = True
			DecreaseBuildArea()


def SettingsClick(button):
	global gameState
	if button.active:
		if button.action == "SAVE":
			pressed = True
			Save(roomPath=saveRoomPath, gameDataPath=saveGamePath)
		if button.action == "LOAD":
			pressed = True
			Load(roomPath=loadRoomPath, gameDataPath=loadGamePath)
		if button.action == "EXACT":
			pressed = True
			ShowExactQuantities()
		if button.action == "SF 1":
			pressed = True
			ChangeResolution(1)
		if button.action == "SF 2":
			pressed = True
			ChangeResolution(2)
		if button.action == "SF 3":
			pressed = True
			ChangeResolution(3)
		if button.action == "EXIT":
			pressed = True
			QuitMenu()


def SaveMenuClick(button):
	global saveNum, gameState, loadRoomPath, loadGamePath, saveRoomPath, saveGamePath, running
	pressed = False
	if button.active:
		if button.action == "BACK":
			gameState = "START MENU"

		for i in range(1, numOFSaveFiles+1):
			if button.action == "SAVE {0}".format(i):
				saveNum = i
				pressed = True

	saveRoomPath = "saves/Save {0}/roomData.json".format(saveNum)
	saveGamePath = "saves/Save {0}/gameData.json".format(saveNum)
	loadRoomPath = "saves/Save {0}/roomData.json".format(saveNum)
	loadGamePath = "saves/Save {0}/gameData.json".format(saveNum)
	return pressed


def LoadMenuClick(button):
	global saveNum, gameState, loadRoomPath, loadGamePath, saveRoomPath, saveGamePath, running
	pressed = False
	if button.active:
		if button.action == "BACK":
			gameState = "START MENU"

		for i in range(1, numOFSaveFiles+1):
			if button.action == "LOAD {0}".format(i):
				saveNum = i
				pressed = True

	loadRoomPath = "saves/Save {0}/roomData.json".format(saveNum)
	loadGamePath = "saves/Save {0}/gameData.json".format(saveNum)
	saveRoomPath = "saves/Save {0}/roomData.json".format(saveNum)
	saveGamePath = "saves/Save {0}/gameData.json".format(saveNum)
	if pressed:
		Load(loadRoomPath, loadGamePath)

	return pressed


def QuitButtonClick(button):
	global gameState
	if button.active:
		if button.action == "YES":
			Quit()
		if button.action == "NO":
			gameState = "NONE"
			for button in allButtons:
				button.active = False


def SliderClicked():
	global sliderMoving
	for slider in allSliders:
		if gameState == "BUILD":
			if slider.type == "BUILD":
				if slider.action == "SCROLL":
					if slider.active:
						sliderMoving = (True, slider)


def ShowExactQuantities():
	for resource in allResources:
		resource.exactAmounts = not resource.exactAmounts


def NewSave():
	global gameState
	gameState = "SAVE MENU"
	CreateSaveMenuObjects()


def LoadSave():
	global gameState
	gameState = "LOAD MENU"
	CreateLoadMenuObjects()


def PrimaryButtonPress(event):
	global gameState
	if gameState != "START MENU":
		if gameState != "SAVE MENU":
			if gameState != "LOAD MENU":
				if event.type == pg.MOUSEBUTTONUP:
					if event.button == 1:
						for button in allButtons:
							if gameState == "CONFIRM QUIT":
								QuitButtonClick(button)
							else:
								if button.active:
									if button.action in allActions:
										gameState = button.action
										# prevent multiple buttons being active
										for b in allButtons:
											if b.type == "GAME":
												if b != button:
													b.active = False
										return
								else:
									if gameState != "BUILD":
										gameState = "NONE"
										CancelBuild()
									else:
										if button.action == "BUILD":
											gameState = "NONE"
											CancelBuild()


def SecondaryButtonPress(event):
	global pressed, sliderMoving
	if event.type == pg.MOUSEBUTTONDOWN:
		if event.button == 1:
			if not pressed:
				if gameState == "NONE":
					HasRoomBeenClicked()

				for button in allButtons:
					if button.active:
						if button.action == "BUILD PAGE DOWN":
							BuildPage("down")
						if button.action == "BUILD PAGE UP":
							BuildPage("up")

					if gameState == "BUILD" and button.type == "BUILD":
						BuildClick(button)

					if gameState == "SETTINGS":
						SettingsClick(button)

				SliderClicked()

	if event.type == pg.MOUSEBUTTONUP:
		if event.button == 1:
			pressed = False
			sliderMoving = (False, False)

	if sliderMoving[0]:
		ScrollBuildMenu(sliderMoving[1])


def IncreaseBuildArea(button):
	global buildPageMax, increaseBuildAreaCost
	for resource in allResources:
		if resource.name == "Caps":
			if resource.value - increaseBuildAreaCost > resource.minAmount:
				if buildPageMax + 1 <= buildPageMaxUpgrade:
					resource.value -= increaseBuildAreaCost
					buildPageMax += 1 
					increaseBuildAreaCost = round(increaseBuildAreaCost * increaseBuildAreaMultiplier)
					button.UpdateExtraText([(increaseBuildAreaCost, ((button.rect.x // SF) + buttonWidth // 2, (button.rect.y // SF) + buttonHeight // 2, buttonWidth, buttonHeight))])


def DecreaseBuildArea():
	global buildPage, buildPageMax, increaseBuildAreaCost
	for resource in allResources:
		if resource.name == "Caps":
			if resource.value + increaseBuildAreaCost < resource.maxAmount:
				decrease = True
				currentBuildPage = buildPage
				for room in allRooms:
					while buildPage < buildPageMax:
						BuildPage("down")
					if room.rect.y == rowHeights[-2]:
						decrease = False

				while buildPage > currentBuildPage:
					BuildPage("up")

				if decrease:
					if buildPageMax - 1 >= buildPageMinUpgrade:
						increaseBuildAreaCost = round(increaseBuildAreaCost / increaseBuildAreaMultiplier)
						resource.value += increaseBuildAreaCost
						buildPageMax -= 1 
						if buildPage > buildPageMax:
							BuildPage("up")

						for button in allButtons:
							if button.action == "INCREASE BUILD AREA":
								button.UpdateExtraText([(increaseBuildAreaCost, ((button.rect.x // SF) + buttonWidth // 2, (button.rect.y // SF) + buttonHeight // 2, buttonWidth, buttonHeight))])


def RoomClicked(room):
	global roomInfoLabels

	if room != False:
		if room.resourcesAvaiable:
			room.CollectResources()
		else:
			for obj in roomInfoLabels:
				if obj in allProgressBars:
					allProgressBars.remove(obj)
			roomInfoLabels = []
			for r in allRooms:
				r.selected = False

			roomNameLabel = Label(mainWindow, (50, 305, 540, 50), "NONE", (colLightGray, room.color), ("{name}: level: {lvl}".format(name=room.name, lvl=room.level), room.color, 14, "top-center"), [True, False, True], [roomInfoLabels])
			x, y, w, h = 500, 315, 30, 30
			if room.level < room.maxLevel:
				upgradeRoom = HoldButton(mainWindow, (x, y, w, h), ("NONE", "UPGRADE ROOM") ,(colWhite, colLightGray), ("Upgrade", colDarkGray), {"room": room}, [roomInfoLabels, allButtons], extraText=[(room.upgradeCost, (x + w // 2, y + h // 2, w, h))])
			roomInfo = HoldButton(mainWindow, (x + w + 10, y, w, h), ("NONE", "ROOM INFO") ,(colWhite, colLightGray), ("Info", colDarkGray), {"room": room}, [roomInfoLabels, allButtons])
			for resource in allResources:
				if room.resourceType == resource.roomType:
					if room.name != "Lift":
						resourceProgressBar = ProgressBar(mainWindow, (90, 330, 400, 15), len(room.seconds) / room.workTime, (room.color, room.color), ("", colLightGray), [True, True], [roomInfoLabels, allProgressBars], [room])
			room.selected = True
	else:
		for obj in roomInfoLabels:
			if obj in allProgressBars:
				allProgressBars.remove(obj)
		roomInfoLabels = []
		for r in allRooms:
			r.selected = False


def UpgradeRoom(button):
	room = button.actionData["room"]
	for joinedRoom in room.joinedRooms:
		for resource in allResources:
			if resource.name == "Caps":
				if resource.value - joinedRoom.upgradeCost / joinedRoom.numOfJoinedRooms >= resource.minAmount:
					resource.value -= joinedRoom.upgradeCost / joinedRoom.numOfJoinedRooms
					joinedRoom.amountSpent += joinedRoom.upgradeCost
					joinedRoom.Upgrade()
					x, y, w, h = button.rect
					x /= SF
					y /= SF
					w /= SF
					h /= SF
					button.UpdateExtraText([(joinedRoom.upgradeCost, (x + w // 2, y + h // 2, w, h))])

	button.actionData = {"room" : room}
	RoomClicked(room)


def ShowRoomInfo(button):
	room = button.actionData["room"]
	room.showingInfo = not room.showingInfo


def CancelBuild():
	if len(tempRooms) > 0:
		tempRooms.pop()


def CheckAllConnections(room):
	leftRect = pg.Rect(room.rect.x - room.rect.w, room.rect.y, room.rect.w, room.rect.h)
	rightRect = pg.Rect(room.rect.x + room.rect.w, room.rect.y, room.rect.w, room.rect.h)
	leftRoom = -1
	rightRoom = -1
	leftRoom = leftRect.collidelist(allRooms)
	rightRoom = rightRect.collidelist(allRooms)
	upRoom = -1
	downRoom = -1
	if room.name == "Lift":
		upRect = pg.Rect(room.rect.x, room.rect.y - room.rect.h, room.rect.w, room.rect.h)
		downRect = pg.Rect(room.rect.x, room.rect.y + room.rect.h, room.rect.w, room.rect.h)
		upRoom = upRect.collidelist(allRooms)
		downRoom = downRect.collidelist(allRooms)

	return leftRoom, rightRoom, upRoom, downRoom


def CheckDemolish(room, direction=(None, None)):
	global demolishList
	remove = False
	leftRoomIndex, rightRoomIndex, upRoomIndex, downRoomIndex = CheckAllConnections(room)
	leftRoom = allRooms[leftRoomIndex]
	rightRoom = allRooms[rightRoomIndex]
	upRoom = allRooms[upRoomIndex]
	downRoom = allRooms[downRoomIndex]
	rooms = [leftRoom, rightRoom, upRoom, downRoom]
	if rooms.count(-1) <= 1:
		# only has one connection
		remove = True
		demolishList.append(room)

	if room not in demolishList:
		demolishList.append(room)
		if room.name == "Lift":
			if direction[1] == None:
				if upRoomIndex != -1:
					CheckDemolish(upRoom, direction=(None, "up"))
				if downRoomIndex != -1:
					CheckDemolish(downRoom, direction=(None, "down"))
			if direction[1] == "up":
				if upRoomIndex != -1:
					CheckDemolish(upRoom, direction=(None, "up"))
			if direction[1] == "down":
				if downRoomIndex != -1:
					CheckDemolish(downRoom, direction=(None, "down"))

		if direction[0] == None:
			if leftRoomIndex != -1:
				CheckDemolish(leftRoom, direction=("left", None))
			if rightRoomIndex != -1:
				CheckDemolish(rightRoom, direction=("right", None))
		if direction[0] == "left":
			if leftRoomIndex != -1:
				CheckDemolish(leftRoom, direction=("left", None))
		if direction[0] == "right":
			if rightRoomIndex != -1:
				CheckDemolish(rightRoom, direction=("right", None))
	else:
		# looped 
		remove = True

	if remove:
		roomToDemolish = demolishList[0]
		for room in allRooms:
			if roomToDemolish in room.joinedRooms:
				room.joinedRooms.remove(roomToDemolish)

		if roomToDemolish in allRooms:
			demolishList = []
			allRooms.remove(roomToDemolish)
			for page in buildingPages:
				if roomToDemolish in page:
					page.remove(roomToDemolish)
			for resource in allResources:
				if roomToDemolish.resourceType == resource.roomType:
					resource.activeRooms -= 1
				if resource.name == "Caps":
					resource.value += roomToDemolish.amountSpent


def DemolishBuild():
	global tempRooms
	for room in allRooms[numOfStartingRooms:]:
		if room.rect.collidepoint(pg.mouse.get_pos()):
			demolishList = []
			CheckDemolish(room)


def AddRoom(roomName):
	room = Room(mainWindow, (0, 0), roomDataFilePath, roomName)
	if len(tempRooms) == 0:
		tempRooms.append(room)
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
	# check total number of bulidings.
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
	for resource in allResources:
		if resource.name == "Caps":
			if resource.value - room.cost >= resource.minAmount:
				resource.value -= room.cost
				room.amountSpent += room.cost
				room.rect = rect
				allRooms.append(room)
				tempRooms.pop()
				placementOptions = []
				index = rowHeights.index(room.rect.y)
				buildingPages[index].append(room)
				for resource in allResources:
					if room.resourceType == resource.roomType:
						resource.activeRooms += 1


def JoinRoom():
	for room in allRooms:
		leftIndex, rightIndex, upIndex, downIndex = CheckAllConnections(room)
		leftRoom, rightRoom = allRooms[leftIndex], allRooms[rightIndex]
		room.UpdateCost()

		if leftIndex != -1:
			if room.joinedRoomMax > 0:
				if leftRoom.name == room.name:
					if leftRoom.level == room.level:
						if len(room.joinedRooms) + 1 <= room.joinedRoomMax:
							if len(leftRoom.joinedRooms) + 1 <= leftRoom.joinedRoomMax:
								for joinedRoom in room.joinedRooms:
									if joinedRoom not in leftRoom.joinedRooms:
										leftRoom.joinedRooms.append(joinedRoom)

								for joinedRoom in leftRoom.joinedRooms:
									if joinedRoom not in room.joinedRooms:
										room.joinedRooms.append(joinedRoom)

		if rightIndex != -1:
			if room.joinedRoomMax > 0:
				if rightRoom.name == room.name:
					if rightRoom.level == room.level:
						if len(room.joinedRooms) + 1 <= room.joinedRoomMax:
							if len(rightRoom.joinedRooms) + 1 <= rightRoom.joinedRoomMax:
								for joinedRoom in room.joinedRooms:
									if joinedRoom not in rightRoom.joinedRooms:
										rightRoom.joinedRooms.append(joinedRoom)

								for joinedRoom in rightRoom.joinedRooms:
									if joinedRoom not in room.joinedRooms:
										room.joinedRooms.append(joinedRoom)


def BuildPage(direction):
	global buildPage
	if direction == "down":
		if buildPage + 1 <= buildPageMax:
			buildPage += 1

			for page in buildingPages: 
				for room in page:
					room.rect.y -= room.rect.h
		else:
			buildPage = buildPageMax


	if direction == "up":
		if buildPage - 1 >= buildPageMin:
			buildPage -= 1

			for page in buildingPages: 
				for room in page:
					room.rect.y += room.rect.h
		else:
			buildPage = buildPageMin
	
	pageBuildNumber.UpdateText(str(buildPage))


def ScrollBuildMenu(direction):
	global buildScrollNum
	if direction == "left":
		if buildScrollNum - 1 >= buildScrollMin:
			buildScrollNum -= 1

			buildScrollSlider.value = buildScrollNum
			buildScrollSlider.ChangeRect()
			
			for button in buildScrollPages:
				button.ChangeRect((button.rect.x + scrollAmount, button.rect.y, button.rect.w, button.rect.h))

	elif direction == "right":
		if buildScrollNum + 1 <= buildScrollMax:
			buildScrollNum += 1

			buildScrollSlider.value = buildScrollNum
			buildScrollSlider.ChangeRect()
			
			for button in buildScrollPages:
				button.ChangeRect((button.rect.x - scrollAmount, button.rect.y, button.rect.w, button.rect.h))

	else:
		slider = direction		
		value = int(slider.value)
		direction = slider.direction

		if buildScrollMin <= value <= buildScrollMax:
			buildScrollNum = value
			for button in buildScrollPages:
				button.ChangeRect((columnWidths[value - 1] + scrollAmount * buildScrollPages.index(button), button.rect.y, button.rect.w, button.rect.h))
				button.rect.x = columnWidths[value - 1] + scrollAmount * buildScrollPages.index(button)


def CheckSaveDirectory():
	rootDirectory = os.getcwd()
	filesInDirectory = [file for file in listdir(os.path.abspath(savePath))]
	saveFileNames = []
	for i in range(1, numOFSaveFiles+1):
		saveFileNames.append("Save {0}".format(i))

	saveDirectoryExistsList = [False for i in range(len(saveFileNames))]
	newDirectorys = []

	for file in filesInDirectory:
		if file in saveFileNames:
			saveDirectoryExistsList[saveFileNames.index(file)] = True

	for i, saveDirectoryExists in enumerate(saveDirectoryExistsList):
		if not saveDirectoryExists:
			newPath = os.path.abspath(savePath) + "\\" + saveFileNames[i]
			os.mkdir(newPath)
			newDirectorys.append(newPath)

	for path in newDirectorys:
		roomData, gameData = SetDeafaultSaveValues() 
		os.chdir(path)

		with open("roomData.json", "w") as saveGameFile:
			json.dump(roomData, fp=saveGameFile, indent=2)

		with open("gameData.json", "w") as saveGameFile:
			json.dump(gameData, fp=saveGameFile, indent=2)

		os.chdir(rootDirectory)


def SetDeafaultSaveValues():
	roomData = {
		"numOfRooms": 0,
		"roomRects": [],
		"roomNames": [],
		"roomIndexs": [],
		"roomLevels": []
	}

	with open(resourceDataFilePath, "r") as resourceDataFile:
		resourceDataValues = json.load(resourceDataFile)
		gameData = {
		"resources": {
			"Water": {
				"value": resourceDataValues["Water"]["value"]["startValue"],
				"activeRooms": 0
			},
			"Food": {
				"value": resourceDataValues["Food"]["value"]["startValue"],
				"activeRooms": 0
			},
			"Power": {
				"value": resourceDataValues["Power"]["value"]["startValue"],
				"activeRooms": 0
			},
			"Caps": {
				"value": resourceDataValues["Caps"]["value"]["startValue"],
				"activeRooms": 0
			}
		},
		"buildPage": buildPageMax
		}

	return roomData, gameData


def Save(roomPath=saveRoomPath, gameDataPath=saveGamePath):
	CheckSaveDirectory()
	SaveRoom(roomPath)
	SaveGameData(gameDataPath)


def Load(roomPath=loadRoomPath, gameDataPath=loadGamePath):
	CreateLoadMenuObjects()
	LoadRoom(roomPath)
	LoadGameData(gameDataPath)


def SaveRoom(path=saveRoomPath):
	for i in range(buildPage):
		BuildPage("up")
	roomData = {
		"numOfRooms": 0,
		"roomRects": [],
		"roomNames": [],
		"roomIndexs": [],
		"roomLevels": []
	}
	for room in allRooms[numOfStartingRooms:]:
		roomData["numOfRooms"] += 1
		x, y, w, h = room.rect
		roomData["roomRects"].append([x // SF, y // SF])
		roomData["roomNames"].append(room.roomName)
		for page in buildingPages:
			if room in page:
				index = buildingPages.index(page)
				break
			else:
				index = None
				break
		if index != None:
			roomData["roomIndexs"].append(index)
		roomData["roomLevels"].append(room.level)

	with open(path, "w") as saveFile:
		json.dump(roomData, fp=saveFile, indent=2)


def SaveGameData(path=saveGamePath):
	gameData = {
	"resources": {
		"Water": {
			"value": 0,
			"activeRooms": 0
		},
		"Food": {
			"value": 0,
			"activeRooms": 0
		},
		"Power": {
			"value": 0,
			"activeRooms": 0
		},
		"Caps": {
			"value": 0,
			"activeRooms": 0
		}
	},
	"buildPage": buildPageMax
	}
	for resource in allResources:
		gameData["resources"][resource.name]["value"] = resource.value
		gameData["resources"][resource.name]["activeRooms"] = resource.activeRooms

	with open(path, "w") as saveFile:
		json.dump(gameData, fp=saveFile, indent=2)


def LoadRoom(path=loadRoomPath):
	global allRooms, buildingPages, buildPage
	allRooms = []
	buildPage = buildPageMin

	AddStartingRooms()
	with open(path, "r") as loadFile:
		roomData = json.load(loadFile)
		for i in range(roomData["numOfRooms"]):
			rect = roomData["roomRects"][i]	
			name = roomData["roomNames"][i]	
			index = roomData["roomIndexs"][i]
			level = roomData["roomLevels"][i]
			room = Room(mainWindow, (rect[0], rect[1]), roomDataFilePath, name)
			room.level = level
			buildingPages[index].append(room)
			allRooms.append(room)


def LoadGameData(path=loadGamePath):
	global buildPageMax
	with open(path, "r") as loadFile:
		gameData = json.load(loadFile)
		buildPageMax = gameData["buildPage"]
		for resource in allResources:
			resource.value = gameData["resources"][resource.name]["value"]
			resource.activeRooms = gameData["resources"][resource.name]["activeRooms"]
			resource.UpdateValue(0)


def QuitMenu():
	global quitConfirmLabels, gameState
	quitConfirmLabels = []
	x, y, w, h = 0, -100, WIDTH // SF, (HEIGHT // SF) + 100
	# background for menu 
	quitConfirmLabels.append(Label(mainWindow, (-100, -100, (WIDTH // 2) + 200, (HEIGHT // 2) + 200), "",(colDarkGray, colDarkGray), ("", colLightGray, 32, "center-center"), lists=[quitConfirmLabels]))
	# main text
	quitConfirmLabels.append(Label(mainWindow, (x, y, w, h), "CONFIRM QUIT",(colDarkGray, colDarkGray), ("Are you sure you want to quit?", colLightGray, 32, "center-center"), lists=[quitConfirmLabels], extraText=[("All data will be saved on exit.", (x + w // 2, y + h // 1.65, 10, 10))]))
	# save and exit
	quitConfirmLabels.append(ToggleButton(mainWindow, ((x + w // 2) - 100 , 240, 200, 50), ("CONFIRM QUIT", "YES"), (colLightGray, colLightGray), ("YES", colDarkGray), lists=[quitConfirmLabels, allButtons], imageData=[buttonPath + "CONFIRM QUIT/YES.png", tempButtonPath + "CONFIRM QUIT/YES.png"]))
	# reject quit
	quitConfirmLabels.append(ToggleButton(mainWindow, ((x + w // 2) - 100 , 300, 200, 50), ("CONFIRM QUIT", "NO"), (colLightGray, colLightGray), ("NO", colDarkGray), lists=[quitConfirmLabels, allButtons], imageData=[buttonPath + "CONFIRM QUIT/NO.png", tempButtonPath + "CONFIRM QUIT/NO.png"]))
	gameState = "CONFIRM QUIT"


def Quit(save=True):
	global running
	running = False
	RoomClicked(False)
	if save:
		Save(roomPath=saveRoomPath, gameDataPath=saveGamePath)


def UpdateAnimations():
	global roomAnimationCounter, roomOverlayAnimationCounter
	if roomAnimationCounter + 1 > roomAnimationDuration:
		roomAnimationCounter = 0
	else:
		roomAnimationCounter += 1

	if roomOverlayAnimationCounter + 1 > roomOverlayAnimationDuration:
		roomOverlayAnimationCounter = 0
	else:
		roomOverlayAnimationCounter += 1


def HandleKeyboard(event):
	global gameState
	if gameState == "SAVE MENU":
		if event.type == pg.KEYDOWN:
			if event.key == pg.K_LEFT:
				ScrollSaveMenu("left")
			if event.key == pg.K_RIGHT:
				ScrollSaveMenu("right")

	elif gameState == "LOAD MENU":
		if event.type == pg.KEYDOWN:
			if event.key == pg.K_LEFT:
				ScrollLoadMenu("left")
			if event.key == pg.K_RIGHT:
				ScrollLoadMenu("right")

	elif gameState != "START MENU" and gameState != "SAVE MENU" and gameState != "LOAD MENU":
		if event.type == pg.QUIT:
			QuitMenu()
		if event.type == pg.KEYDOWN:
			if event.key == pg.K_ESCAPE:
				QuitMenu()
		if event.type == pg.KEYDOWN:
			if event.key == pg.K_UP:
				BuildPage("up")
			if event.key == pg.K_DOWN:
				BuildPage("down")

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


def StartGame():
	global running, gameState
	running = True
	CreateButtons()
	CreateResources()
	AddStartingRooms()
	GetBuildPageRowHeights()
	GetBuildScrollColumnWidths()
	pageBuildNumber.UpdateText(str(buildPage))
	gameState = "NONE"
	DrawLoop()

	while running:
		clock.tick(FPS)
		for event in pg.event.get():
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

		for resource in allResources:
			resource.CalculateTime()
		for room in allRooms:
			if room.resource != None:
				room.Timer()

		DrawLoop()
		UpdateAnimations()
		JoinRoom()


def StartMenu():
	CreateStartMenuObjects()
	running = True
	startGame = True
	pressed = False
	while running:
		clock.tick(FPS)
		for event in pg.event.get():
			if event.type == pg.QUIT:
				running = False
				startGame = False
			if event.type == pg.KEYDOWN:
				if event.key == pg.K_ESCAPE:
					running = False
					startGame = False

			HandleKeyboard(event)

			for button in allButtons:
				button.HandleEvent(event)
		
		if gameState == "START MENU":
			for obj in startMenuObjects:
				if obj in allButtons:
					if obj.active:
						if obj.action == "QUIT":
							running = False
							startGame = False
						if obj.action == "SAVE MENU":
							# running = False
							NewSave()
						if obj.action == "LOAD MENU":
							# running = False
							LoadSave()

		for button in allButtons:
			if gameState == "SAVE MENU":
				pressed = SaveMenuClick(button)
			if gameState == "LOAD MENU":
				pressed = LoadMenuClick(button)
			button.active = False
			if pressed:
				running = False

		DrawStartMenu()

	if startGame:
		StartGame()

CheckSaveDirectory()
StartMenu()

pg.quit()
