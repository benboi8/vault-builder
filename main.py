import pygame as pg
from pygame import gfxdraw
import datetime as dt
import cv2
import json
from PIL import Image

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

saveRoomPath = "saves/roomData.json"
loadRoomPath = "saves/roomData.json"
saveGamePath = "saves/gameData.json"
loadGameData = "saves/gameData.json"


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

# settings button info
settingsButtonListData = [
("Save", "save", "SAVE"),
("Load", "load", "LOAD"),
("Exact", "exact", "EXACT"),
("640x360", "SF 1", "SF 1"),
("1280x720", "SF 2", "SF 2"),
("1920x1080", "SF 3", "SF 3"),
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

boundingRect = pg.Rect(50.5 * SF, 50.5 * SF, 550 * SF, 249 * SF)
scrollCollideingRect = pg.Rect(50 * SF, 310 * SF, 500 * SF, 30 * SF)

# determines what can be done in game e.g. building rooms
gameState = "NONE"
# primary button actions e.g. build button
allActions = ["BUILD", "SETTINGS"]
buttonWidth, buttonHeight = 30, 30

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
	if not additive:
		x += radius
		w -= radius * 2
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


def ResizeImage(imagePath, imageScale, newImagePath):
	image = Image.open(imagePath)
	image = image.resize((imageScale[0], imageScale[1]), Image.ANTIALIAS)
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
	def __init__(self, surface, rect, buttonType, colorData, textData, actionData={}, lists=[allButtons]):
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
		for listToAppend in lists:
			listToAppend.append(self)

		self.Rescale()

	def Rescale(self):
		self.rect = pg.Rect(self.originalRect[0] * SF, self.originalRect[1] * SF, self.originalRect[2] * SF, self.originalRect[3] * SF)

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
		self.actionData = actionData
		for listToAppend in lists:
			listToAppend.append(self)
		self.Rescale()

	def Rescale(self):
		self.rect = pg.Rect(self.originalRect[0] * SF, self.originalRect[1] * SF, self.originalRect[2] * SF, self.originalRect[3] * SF)

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
		allSliders.append(self)

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
		if event.type == pg.MOUSEBUTTONDOWN:
			if event.button == 1:
				mousePos = pg.mouse.get_pos()
				if self.collisionRect.collidepoint(mousePos):
					self.active = True

		if event.type == pg.MOUSEBUTTONUP:
			if event.button == 1:
				self.active = False

		if self.active:
			self.sliderColor = self.activeColor
			self.MoveSlider()
		else:
			self.sliderColor = self.inactiveColor

		self.textSurface = self.font.render(self.text, True, self.textColor)

	def MoveSlider(self):
		motion = pg.mouse.get_rel()
		if motion[0] <= 0:
			self.direction = "left"
		elif motion[0] > 0:
			self.direction = "right"

		mousePosX = pg.mouse.get_pos()[0]
		if mousePosX < self.rect.x + self.rect.w - self.sliderRect.w // 2:
			if mousePosX > self.rect.x + self.sliderRect.w // 2:
				self.sliderRect.x = mousePosX - self.sliderRect.w // 2
				self.ChangeValue()
		self.collisionRect = pg.Rect(self.sliderRect.x - self.sliderRect.h // 2, self.sliderRect.y, self.sliderRect.w + self.sliderRect.h, self.sliderRect.h)
		self.textSurface = FONT.render(self.text, True, self.textColor, self.sliderColor)

	def ChangeValue(self):
		self.value = max(round(((self.sliderRect.x - self.rect.x) / self.rect.w) * (self.bounds[1] + 1), 0), self.bounds[0])

	def ChangeRect(self):
		self.sliderRect.x = self.value * self.segmentLength


class ProgressBar:
	def __init__(self, surface, rect, percentageFilled, colorData, textData, drawData=[False, False], lists=[allProgressBars], extraData=[]):
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
	def __init__(self, surface, rect, gameStateType, colors, textData, drawData=[False, False, True],lists=[allLabels]):
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

		self.Rescale()

		for listToAppend in lists:
			listToAppend.append(self)

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

	def Draw(self):
		if self.roundedEdges:
			DrawObround(mainWindow, self.backgroundColor, self.rect, self.filled, self.additive)
			DrawObround(mainWindow, colDarkGray, (self.rect.x + 3, self.rect.y + 3, self.rect.w - 6, self.rect.h - 6), self.filled, self.additive)
		else:
			pg.draw.rect(mainWindow, self.backgroundColor, self.rect)
			if self.borderColor != False:
				DrawRectOutline(mainWindow, self.borderColor, self.rect, 3 * SF)
		self.surface.blit(self.textSurface, self.textRect)

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
		self.workPeriod = roomData["resource"]["time"]
		self.level = roomData["levelData"]["level"]
		self.maxLevel = roomData["levelData"]["maxLevel"]
		self.baseCost = roomData["levelData"]["baseCost"]
		self.levelCostFunction = roomData["levelData"]["levelCostFunction"]
		self.joinedRooms = roomData["levelData"]["joinedRooms"]
		self.joinedRoomLevel = roomData["levelData"]["joinedRoomLevel"]
		self.dwellersWorking = roomData["dwellers"]

		self.selected = False
		self.showingInfo = False
		self.resource = None
		for resource in allResources:
			if self.resourceType == resource.roomType:
				self.resource = resource

		self.image = roomData["drawData"]["image"]

		self.text = self.name
		self.textSurface = FONT.render(self.text, True, self.textColor)

		self.hasImage = False
		self.Rescale()

		self.seconds = []
		self.counter = 0
		self.CalculateCosts()

	def Rescale(self):
		self.width, self.height = roomWidth * self.roomData["dimensions"]["width"] * SF, roomHeight * self.roomData["dimensions"]["height"] * SF
		self.rect = pg.Rect(self.pos[0] * SF, self.pos[1] * SF, self.width, self.height)

	def CalculateCosts(self):
		self.cost = self.baseCost
		self.upgradeCost = self.baseCost

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
			self.text = "{name}: {value:,}".format(name=self.name, value=self.value)
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
		DrawObround(self.surface, self.color, self.rect)
		if self.drawFilled:
			# draw filled amount
			self.DrawAmount()
			self.surface.blit(self.textSurface, (self.rect.x + self.rect.w // 2- self.textSurface.get_width() // 2, (self.rect.y - self.rect.h // 2) - 2.5 * SF))
		else:
			# draw text
			self.surface.blit(self.textSurface, (self.rect.x + self.rect.w // 2- self.textSurface.get_width() // 2, self.rect.y + self.rect.h // 2 - self.textSurface.get_height() // 2))

		if self.exactAmounts:
			self.text = "{name}: {value:,}".format(name=self.name, value=self.value)
			self.textSurface = FONT.render(self.text, True, self.color)
		else:
			self.text = "{name}".format(name=self.name)
			self.textSurface = FONT.render(self.text, True, self.color)

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
			self.text = "{name}: {value:,}".format(name=self.name, value=self.value)

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
			self.AddResource()
			self.MinusResource()
			if self.drawFilled:
				self.text = "{name}".format(name=self.name)
			else:
				self.text = "{name}: {value:,}".format(name=self.name, value=self.value)

			self.textSurface = FONT.render(self.text, True, self.textColor)
			self.UpdateRect()

	def AddResource(self):
		if self.value + self.valuePerMin * self.activeRooms <= self.maxAmount:
			self.value += self.valuePerMin * self.activeRooms
		else:
			self.value = self.maxAmount

	def MinusResource(self):
		if self.value - max(self.usage, self.usage * len(allDwellers)) >= self.minAmount:
			self.value -= max(self.usage, self.usage * len(allDwellers))
		else:
			self.value = self.minAmount


def CreateResources():
	global waterResource, foodResource, powerResource, moneyResource
	x, y, w, h = 200, 10, 40, 15
	for resource in resourceList:
		waterResource = Resource(mainWindow, (x, y, w, h), resource, resourceDataFilePath)
		x += 60


def CreateButtons():
	global pageUpBuildButton, pageBuildNumber, pageDownBuildButton
	CreateBuildingButtons()
	CreateSettingsButtons()
	pageUpBuildButton = HoldButton(mainWindow, (605, (360 // 2) - 55, buttonWidth, buttonHeight), ("GAME", "BUILD PAGE UP"), (colWhite, colLightGray), ("Up", colDarkGray))
	pageBuildNumber = Label(mainWindow, (605, 360 // 2 - 15, buttonWidth, buttonHeight), "GAME", (colLightGray, colDarkGray), (buildPage, colLightGray, 24, "center-center"))
	pageDownBuildButton = HoldButton(mainWindow, (605 , (360 // 2) + 25, buttonWidth, buttonHeight), ("GAME", "BUILD PAGE DOWN"), (colWhite, colLightGray), ("Down", colDarkGray))


def CreateBuildingButtons():
	global cancelBuildButton, demolishBuildButton, buildButton, buildScrollSlider
	# building button
	startX, startY = 10, 310
	buildButton = ToggleButton(mainWindow, (startX, startY, buttonWidth, buttonHeight), ("GAME", "BUILD"), (colWhite, colLightGray), ("Build", colDarkGray))
	x = startX
	for buttonData in buildingButtonListData:
		x += buttonWidth + 5 * SF
		name = buttonData[0]
		actionData = buttonData[1]
		color = roomColors["col" + name + "Room"]
		roomButton = HoldButton(mainWindow, (x, startY, buttonWidth, buttonHeight), ("BUILD", "ADD ROOM"), (color, color), (name, colDarkGray), actionData) 
		buildScrollPages.append(roomButton)

	cancelBuildButton = HoldButton(mainWindow, (10, 230, buttonWidth, buttonHeight), ("BUILD", "INCREASE BUILD AREA"), (colGreen, colLightGreen), ("Expand", colDarkGray))
	cancelBuildButton = HoldButton(mainWindow, (10, 270, buttonWidth, buttonHeight), ("BUILD", "CANCEL"), (colRed, colCancel), ("Cancel", colDarkGray))
	demolishBuildButton = ToggleButton(mainWindow, (595, 315, buttonWidth + 10, buttonHeight + 10), ("BUILD", "DEMOLISH"), (colRed, colDemolish), ("Demolish", colDarkGray))

	buildScrollSlider = Slider(mainWindow, (50, 348, 530, 10), ("BUILD", "SCROLL"), (colLightGray, colWhite, colLightGray), (" ||| ", colDarkGray, 8), (buildScrollMin, buildScrollMax))


def CreateSettingsButtons():
	startX, startY = 10, 10
	settingsButton = ToggleButton(mainWindow, (startX, startY, buttonWidth, buttonHeight), ("GAME", "SETTINGS"), (colWhite, colLightGray), ("Settings", colDarkGray))
	y = startY
	for buttonData in settingsButtonListData:
		y += buttonHeight + 5 * SF
		name = buttonData[0]
		actionData = buttonData[1]
		buttonAction = buttonData[2]
		color = (colWhite, colLightGray)
		settingsButton = HoldButton(mainWindow, (startX, y, buttonWidth, buttonHeight), ("SETTINGS", buttonAction), color, (name, colDarkGray), actionData)


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

	pg.display.update()


def DrawRooms():
	for page in buildingPages:
		for room in page:
			if boundingRect.colliderect(room.rect):
				room.Draw()


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
			IncreaseBuildArea()


def SettingsClick(button):
	if button.active:
		if button.action == "SAVE":
			pressed = True
			Save()
		if button.action == "LOAD":
			pressed = True
			Load()
		if button.action == "EXACT":
			pressed = True
			ShowExcatQuantities()
		if button.action == "SF 1":
			pressed = True
			ChangeResolution(1)
		if button.action == "SF 2":
			pressed = True
			ChangeResolution(2)
		if button.action == "SF 3":
			pressed = True
			ChangeResolution(3)


def SliderClicked():
	global sliderMoving
	for slider in allSliders:
		if gameState == "BUILD":
			if slider.type == "BUILD":
				if slider.action == "SCROLL":
					if slider.active:
						sliderMoving = (True, slider)


def ShowExcatQuantities():
	for resource in allResources:
		resource.exactAmounts = not resource.exactAmounts


def PrimaryButtonPress(event):
	global gameState
	if event.type == pg.MOUSEBUTTONUP:
		if event.button == 1:
			for button in allButtons:					
				if button.active:
					if button.action in allActions:
						gameState = button.action
						return
				else:
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

					if gameState == "BUILD":
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


def IncreaseBuildArea():
	global buildPageMax
	# cost check
	if buildPageMax + 1 <= buildPageMaxUpgrade:
		buildPageMax += 1 


def RoomClicked(room):
	global roomInfoLabels
	for obj in roomInfoLabels:
		if obj in allProgressBars:
			allProgressBars.remove(obj)
	roomInfoLabels = []
	roomInfoLabels = []
	for r in allRooms:
		r.selected = False			

	if room != False:
		roomNameLabel = Label(mainWindow, (50, 305, 540, 50), "NONE", (colLightGray, room.color), ("{name}: level: {lvl}".format(name=room.name, lvl=room.level), room.color, 14, "top-center"), [True, False, True], [roomInfoLabels])
		upgradeRoom = HoldButton(mainWindow, (500, 315, 30, 30), ("NONE", "UPGRADE ROOM") ,(colWhite, colLightGray), ("Upgrade", colDarkGray), {"room": room}, [roomInfoLabels, allButtons])
		roomInfo = HoldButton(mainWindow, (540, 315, 30, 30), ("NONE", "ROOM INFO") ,(colWhite, colLightGray), ("Info", colDarkGray), {"room": room}, [roomInfoLabels, allButtons])
		for resource in allResources:
			if room.resourceType == resource.roomType:
				if room.name != "Lift":
					resourceProgressBar = ProgressBar(mainWindow, (90, 330, 400, 15), len(resource.seconds) / resource.workTime, (room.color, room.color), ("", colLightGray), [True, True], [roomInfoLabels, allProgressBars], [resource])
		room.selected = True


def UpgradeRoom(button):
	room = button.actionData["room"]
	maxLevel = room.maxLevel
	if room.level + 1 <= maxLevel:
		for resource in allResources:
			if resource.name == "Caps":
				if resource.value - room.upgradeCost >= resource.minAmount:
					resource.value -= room.upgradeCost
					room.level += 1
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


def DemolishBuild():
	for room in allRooms[numOfStartingRooms:]:
		if room.rect.collidepoint(pg.mouse.get_pos()):
			leftRoom, rightRoom, upRoom, downRoom = CheckAllConnections(room)
			remove = True
			if remove:
				allRooms.remove(room)
				for page in buildingPages:
					if room in page:
						page.remove(room)
				for resource in allResources:
					if room.resourceType == resource.roomType:
						resource.activeRooms -= 1
					if resource.name == "Caps":
						resource.value += (room.upgradeCost * (room.level - 1)) + room.cost			

def AddRoom(roomName):
	room = Room(mainWindow, (0, 0), roomDataFilePath, roomName)
	for resource in allResources:
		if resource.name == "Caps":
			if resource.value - room.cost >= resource.minAmount:
				resource.value -= room.cost
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
	for resource in allResources:
		if room.resourceType == resource.roomType:
			resource.activeRooms += 1


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


def Save():
	SaveRoom()
	SaveGameData()


def Load():
	LoadRoom()
	LoadGameData()


def SaveRoom(path=saveRoomPath):
	for i in range(buildPage):
		BuildPage("up")
	roomData = {
		"numOfRooms": 0,
		"roomRects": [],
		"roomNames": [],
		"roomIndexs": []
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
		roomData["roomIndexs"].append(index)

	with open(path, "w") as saveFile:
		json.dump(roomData, fp=saveFile, indent=2)


def SaveGameData(path=saveGamePath):
	gameData = {
		"resources": {},
		"buildPage": buildPageMax
	}
	for resource in allResources:
		gameData["resources"][resource.name] = resource.value

	with open(path, "w") as saveFile:
		json.dump(gameData, fp=saveFile, indent=2)


def LoadRoom(path=loadRoomPath):
	global allRooms, buildingPages, buildPage
	allRooms = []
	buildingPages = [[] for i in range(buildPageMin, buildPageMax)]
	buildPage = buildPageMin
	pageBuildNumber.UpdateText(str(buildPage))

	AddStartingRooms()
	with open(path, "r") as loadFile:
		roomData = json.load(loadFile)
		for i in range(roomData["numOfRooms"]):
			rect = roomData["roomRects"][i]	
			name = roomData["roomNames"][i]	
			index = roomData["roomIndexs"][i]
			room = Room(mainWindow, (rect[0], rect[1]), roomDataFilePath, name)
			buildingPages[index].append(room)
			allRooms.append(room)


def LoadGameData(path=loadGameData):
	global buildPageMax, allResources
	with open(path, "r") as loadFile:
		gameData = json.load(loadFile)
		buildPageMax = gameData["buildPage"]
		for resource in allResources:
			resource.value = gameData["resources"][resource.name]
			resource.UpdateValue(0)


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

		for resource in allResources:
			if event.key == pg.K_EQUALS:
				resource.UpdateValue(10)
			if event.key == pg.K_MINUS:
				resource.UpdateValue(-10)
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

	for room in allRooms:
		for resource in allResources:
			if room.resourceType == resource.roomType:
				resource.CalculateTime()

	DrawLoop()
