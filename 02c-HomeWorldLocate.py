#!/usr/bin/python
'''
PLANETS.NU UTILITY
LOCATE LIKELY HOMEWORLD POSITIONS ON STARMAP

Parse through the planet coordinates and calculate which planets meet the criteria
for "homeworld" location based on distance from neighboring planets.

Generates a planet distance matrix and then sorts through those distances looking
for candidates that meet the HW settings used in the game setup algorithm.

Outputs tables for R plotting to show most likely HW positions along with all
possible HW positions. Take these positions as close, not exact, position locations. 

Uses the TURN file data downloaded by script "01-DownLoadTurnFiles.py" with this
directory structure:

.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 
PWD - -
    | 001-GameData  >                                   - folder with ALL Game Data
                | 141666-Kattia >                       - game name folder (ID + sector name)
                        | 001-TurnFiles >               - folder with just turn data files               
                                | 001-TurnData.txt      - unzip'd json files prefixed with turn number
                                | 002-TurnData.txt      -    . . .
                                | 003-TurnData.txt
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .

hijk/2015/2018/2019
'''
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
import sys, re, os
import json
from collections import defaultdict
import subprocess

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# - - - - -   U S E R  V A R I A B L E S  - - - - - - - - - - - - -
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Current Sector Details . . . . . . . . . .
gameName  = '317153-Ultramax9999UnlimitedI' + '/'    #  folder in gameData with THIS game's turn folders
gameData  = '001-GameData'    + '/'    #  folder in PWD where game data is stored
starBase  = 'p000'  # 'p000' = look it up in current turn file; else, set a specific reference planet.

# Run Control Parameters . . . . . . . . . . 
pauseRun  = 0       # 1 = wait after each iteration so you can read screen info; 0 = no wait
plotMap   = 1       # 1 = run R script to generate starchart map; 0 = no map plot
scrdump   = 1       # formatted table output

# Set the distance parameters for assessing HW distributions in cluster . . . .
hwDist     = 450     # 450, expected average distance between HWs 
minDist    = 425     # 425, shortest distance between two homeworlds
maxDist    = 550     # greatest distance between two homeworlds
cminDIST   = 400     # closest possible distance from center of cluster
cmaxDIST   = 1000    # maximum
verycloseD = 82      # round up
closeD     = 163     # round up 
maxPlanets = 600     # Ridculous max limit on number of possible planet ID values in sector
                     #   This is important when nebulae and debris disks are in play and
                     #   the range of ID numbers is actually > than the number of planets
                     #   specified in game settings.

# # Old vars that are now input from game files . . . . . .
# cx         = 1950    # center x coord
# cy         = 1950    # center y coord
# planet81   = 3       #  "verycloseplanets" = setup value for minimum planets within 81 LY
# planet162  = 12      #  "closeplanets"     = setup value for minimum planets between 81 and 162 LY
# numberHW  = 12      # number of HWs to locate (= number of players)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# - - - - -   G L O B A L  V A R I A B L E S  - - - - - - - - - - - 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Fixed variables . . . . . 
turnFolder = '001-TurnFiles'       # default folder for dumping turn files
turnFile   = '001-TurnData.txt'    # default file name for turn number 1, using '001' tag format
gameFolder = gameData + gameName   # '00-GameData/127256-SmithsWorld/'

# R plot script for starchart . . . . . 
ggplotR   = "21-HomeWorldMap.R"       # R plotting script
Rwrapper  = "/usr/local/bin/Rscript"    # osx
Rargs     = "--vanilla"

# Initialize VARS . . . . . . . . 
planData = defaultdict(lambda: defaultdict(lambda: 'unk'))
planKeys = ["id", "name", "x", "y"]
dMatrix = defaultdict(lambda: defaultdict(lambda: 0))
dCenter = []
shortListWorlds = []
homeWorlds = []
planData['unk']['name'] = 'unk'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - -   M  A  I  N  - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

print "\n\nRunning HomeWorld Location Matrix . . . . . . "
print "     Game: ", gameData
print "     Turn:  001"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# 1. Read the json game data file for tunr 001 . . . . .  . . . . .
IN=open("%s%s/%s" % (gameFolder,turnFolder, turnFile), 'r')
jsonRaw = IN.readline()
IN.close()
gameJson = json.loads(jsonRaw)
numPlans = len(gameJson['rst']['planets'])
print("         race id num           = %s" % gameJson['rst']['player']['raceid'])
print("         player number in game = %s" % gameJson['rst']['player']['id'])

if (gameJson['rst']['settings']['hwdistribution'] != 2):
    print("**********\nDoes not look like the right HW Distribution for this algorithm.\n****************\n\n")
    sys.exit()

planet81  = gameJson['rst']['settings']['verycloseplanets']
planet162 = gameJson['rst']['settings']['closeplanets']
numberHW  = len(gameJson['rst']['players'])
print("numberHW = %d"%numberHW)
cx = 0
cy = 0
for i in range(numPlans):
    cx += gameJson['rst']['planets'][i]['x']/float(numPlans)
    cy += gameJson['rst']['planets'][i]['y']/float(numPlans)
print("cx,cy = %0.1f,%0.1f"%(cx,cy))

if (starBase == 'p000'):
    for i in range(numPlans):
        if (gameJson['rst']['planets'][i]['ownerid'] == gameJson['rst']['player']['id']):
            if (gameJson['rst']['starbases'][0]['planetid'] == gameJson['rst']['planets'][i]['id']):
                starBase = "p" + str(gameJson['rst']['planets'][i]['id'])
            else:
                print("\n\nError locating your HW starbase. Hard Exit.\n\n")
                sys.exit()
    print("         HW starbase located: %s\n" % starBase)
homeWorlds.append(starBase)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# 2. Cycle through the planets and extract the IDs and x,y coords . . . . . .

# Filter out debrisdisk planetoids . . . .
planetIDs = []
Pindex    = {}
for i in range(maxPlanets):
    try:
        if gameJson['rst']['planets'][i]['debrisdisk'] == 0:
            pid = "p" + str(gameJson['rst']['planets'][i]['id'])
            planetIDs.append(pid)
            Pindex[pid] = i
    except:
        break
Nplan = len(planetIDs)   # < number of visible planets with known coordinates
print "There are %d visible planets in this sector map." % Nplan

# Build a PLANET Dictionary where all ID numbers from 1 to Nplan have an entry
# Need to identify missing planets in nebulae and planetoids in debris disks . . . . 
gap = 0
debriscount = 0
nebulacount = 0
for pid in planetIDs:
    for key in planKeys:
        planData[pid][key] = gameJson['rst']['planets'][Pindex[pid]][key]
    # Add key for HW designation
    planData[pid]['HW'] = 'no'
    if (pid == starBase):
        print "\nHomeWorld Data Check:"
        print "%s\t%s\t%s\t%s\n" % (pid, planData[pid]['name'], planData[pid]['x'], planData[pid]['y'] )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# 3. Calculate distance from center of sector . . . . . . . . .
#    Make this value the first 0 row in distance matrix
#dMatrix["p0"] = {}
dMatrix["p0"]["p0"] = 0
for pid in planetIDs:
    x1 = float(planData[pid]['x'])
    y1 = float(planData[pid]['y'])
    cd = ((x1-cx)**2 + (y1-cy)**2)**0.5
    dMatrix["p0"][pid] = round(cd)   # store distance of each planet from center

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# 4. Calculate distance matrix . . . . . . .. . 
mi = 1
for pid in planetIDs:
    x1 = float(planData[pid]['x'])
    y1 = float(planData[pid]['y'])
    dMatrix[pid] = {}
    dMatrix[pid]["p0"] = -1     # just make the 0 col a "-1" 
    for pjd in planetIDs:
        x2 = float(planData[pjd]['x'])
        y2 = float(planData[pjd]['y'])
        d = ((x1-x2)**2 + (y1-y2)**2)**0.5
        dMatrix[pid][pjd] = round(d)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# 5. Find the right distance distributions for potential homeworlds . . . . .
hcount = 0
for pi in planetIDs:
    if dMatrix["p0"][pi] > cminDIST and dMatrix["p0"][pi] < cmaxDIST:         # < distance from center @ (2000, 2000)
        count81 = 0
        count162 = 0
        for pj in planetIDs:
            if dMatrix[pi][pj] > 1 and dMatrix[pi][pj] < verycloseD:
                count81 += 1
            elif dMatrix[pi][pj] >= verycloseD and dMatrix[pi][pj] <= closeD:
                count162 += 1
        #     if pi == 158 and dMatrix[pi][pj] < 175:
        #         print pj, dMatrix[pi][pj]        
        # if pi == 158:
        #     print count81, count162
        #     sys.exit()
        if count81 == planet81 and count162 >= planet162:
            if not (pi in shortListWorlds):
                shortListWorlds.append(pi)
                planData[pi]["count162"] = count162
                planData[pi]["HW"] = 'possible'
                hcount += 1
            # print "%d\t%s\t%s\t%s" % (pi, planData[pi]['name'], planData[pi]['x'], planData[pi]['y'] )
print "There are %d possible homeworld locations." % hcount
print shortListWorlds
# sys.exit()

# Purge the shortListWorlds of planets around the REFERENCE HW position . . . .
tooclose=[]
for id in shortListWorlds:
   d = dMatrix[starBase][id]
   if d > 1 and d < minDist:
       tooclose.append(id)
for tc in tooclose:
   shortListWorlds.remove(tc)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# 6. Parse through the HW distance matrix looking for the most likely possible spacing
#- --- -- --- - - - ------  - - - - --- -- -- --  - - ---- -- -- -  --  -- -- -
# 190217 - Rebuild the algorithm approach for finding HomeWorlds.
# Just start with finding the HW's that are neighboring my starting HomeWorld.
# Think of the task as focusing on a KNOWN homeworld position and solving for the
#     the positions of the two most likely HWs around your SB location. It boils down
#     to just a 3 planet analysis. Once you identify your HW neighbors. Then the next
#     iteration is to solve for one of those neighborss neighboring HW system GIVEN
#     the two HW positions you already know . . . . yours and neighbor1 . . . now solve
#     for neighbor2.
print "\nLocating most likely homeworld positions . . . . "
HWcount = 0
print("%d:  %s\t%s\t\t < known StarBase HomeWorld" % (HWcount+1, starBase, planData[starBase]['name']))
planData[starBase]['HW'] = 'HomeWorld'
hwArray = []
for i in range(numberHW):
    hwArray.append('unk')
centerindex = int(numberHW/2)
hwArray[centerindex] = starBase     # initialize with first known HW location in center of list
flow = 1                            # starting value for first iteration 
done = 0
slw = list(shortListWorlds)
lastHB = 'na'
switchcount = 0
targetdistance = hwDist
while(done == 0):
    # Flow control between iterations needs to set the CURRENT TARGET position
    if (len(homeWorlds) == 1):
        ci = centerindex          # first iteration is easy; starts with player's HW  
    
    elif (flow == 1):
        for i in range(0, numberHW):
            j = centerindex + i      # start at center position
            if (j > (numberHW-1)):   # cycle back to beginning of hwArray if needed
                j = j - numberHW
            # find next empty slot, then set target to the last defined slot
            if hwArray[j] == 'unk':
                ci = j - 1   # last defined index position in hwArray
                if (ci == -1):
                    ci = numberHW - 1
                break
            
    elif (flow == -1):
        for i in range((numberHW-1), 0, -1):
            j = i - centerindex - 1
            if (j < 0):
                j = numberHW + j 
            # find next empty slot, then set target to the last defined slot
            if hwArray[j] == 'unk':
                ci = j + 1   # last defined index position in hwArray
                if (ci == numberHW):
                    ci = 0
                break    
  
    # 1. CURRENT TARGET: Find possible planets within the right distance . . . .
    homebase = hwArray[ci]
    distDict = defaultdict(lambda: -1)
    dist     = []
    for spid in slw:
        if not spid in homeWorlds:
            if (dMatrix[homebase][spid] > 0):
                d = dMatrix[homebase][spid]
            if d >= minDist and d <= maxDist:
                dist.append(d)
                distDict[spid] = d
    print "There are %d planets in range of %s that are possible candidates.\nThe most likely neighbors are:" % (len(dist), homebase)
    for (pid,d) in sorted(distDict.items(), key=lambda x:x[1]):
        print "    %s = %0.1f" % (pid,d)


    # 2. Find first HW neighbor to the TARGET position . . . . . .
    refpos1 = 'unk'
    # use refpos1 as the known neighbor of the CURRENT TRAGET . . . 
    r1i = ci - (1*flow)
    if (r1i == -1):       r1i = (numberHW-1)
    if (r1i == numberHW): r1i = 0    
    refpos1 = hwArray[r1i]
    # print(ci, r1i, refpos1)
    # but if not yest defined, then locate . . . . . . this loop only active at first iteration
    if (refpos1 == 'unk'):
        td = targetdistance
        mind = 999
        for (pid,d) in sorted(distDict.items(), key=lambda x:x[1]):
                delta = abs(d - td)
                if (delta < mind):
                    refpos1 = pid
                    mind = delta
        homeWorlds.append(refpos1)
        planData[refpos1]['HW']     = 'StarBase'
        HWcount += 1
        hwArray[ci - 1] = refpos1
        print "      FOUND1: %s @ %0.0f ly" % (refpos1, dMatrix[refpos1][homebase])       
        #Purge the shortListWorlds of planets around the REFERENCE HW position . . . .
        tooclose=[]
        for id in slw:
           d = dMatrix[refpos1][id]
           if d > 1 and d < 0.75*minDist:
               tooclose.append(id)
        for tc in tooclose:
           slw.remove(tc)
    else:
        print "      neighbor1: %s @ %0.0f ly" % (refpos1, dMatrix[refpos1][homebase]) 

    r1i = hwArray.index(refpos1)
    r2i = ci + (1*flow)
    if (r1i > ci and r1i != (numberHW-1)):        r2i = ci - 1
    if (r2i == -1):                               r2i = (numberHW-1)
    if (r2i == numberHW):                         r2i = 0
    
    # 3. Find second HW neighbor to the TARGET position . . . . . . 
    refpos2 = 'unk'
    # targetdistance = [450] #, 520]
    # for td in targetdistance:
    td = targetdistance
    maxd = 0
    mind = 999
    delta = 999
    for (pid,d) in sorted(distDict.items(), key=lambda x:x[1]):
        delta = abs(d - td)
        #if (d > maxd and pid != refpos1):
        if (delta < mind and pid != refpos1):
            if (dMatrix[refpos1][pid] > 600 and dMatrix[refpos1][pid] < 1050):
                refpos2 = pid
                maxd = d
                mind = delta
        #print(">>> %s: %d" % (td, mind))
        # if (mind < 10):   # first see if close match to 450 ly exists
        #     break

    if (refpos2 == 'unk'):
        print "          NO TARGET: %s has no 2nd neighbor located" % homebase
        flow = flow*-1      # reverse direction of search in hwArray . . . . .
        switchcount += 1
        if (switchcount % 2 == 0):
            targetdistance += 25
            maxDist += 15

    elif (not refpos2 in homeWorlds):
        homeWorlds.append(refpos2)
        planData[refpos2]['HW']     = 'StarBase'
        hwArray[r2i] = refpos2
        print "      FOUND2: %s @ %0.0f ly" % (refpos2, dMatrix[refpos2][homebase]) 
        print "          distance between %s & %s =  %0.0f ly" % (refpos1, refpos2, dMatrix[refpos1][refpos2])

        #Purge the shortListWorlds of planets around known HW position . . . .
        tooclose=[]
        for id in slw:
           d = dMatrix[refpos2][id]
           if d > 1 and d < 0.75*minDist:
               tooclose.append(id)
        for tc in tooclose:
           slw.remove(tc)
        
        print hwArray
        print homeWorlds

    if (pauseRun == 1):
        wait = raw_input("\n\n<press enter to continue> . . . . \n")
    
    if lastHB != homebase:
        lastHB = homebase
    else:
        done = 1
    
    if switchcount > 6:
        done = 1
    
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# 7. Screen Report for likely homeworlds . . . . . .
if (scrdump == 1):
    printLines = []
    row = [ "", "", "", "Neighbors:", ""]
    printLines.append(row)
    row = ["Num", "pID", "HomeWorld", "Dist1", "Dist2" ]
    printLines.append(row)
    row = ["-----", "-----", "---------", "-----", "-----"]
    printLines.append(row)
    border = row
    for j in range(numberHW):
        hw = hwArray[j]
        k = j - 1
        m = j + 1
        if (k == -1): k = numberHW-1
        if (m == numberHW): m = 0
        n1 = hwArray[k]
        n2 = hwArray[m]
        if hw != 'unk':
            if n1 == 'unk':
                n1d = "na"
            else:
                n1d = str("%0.1fly"%dMatrix[hw][n1])
            if n2 == 'unk':
                n2d = "na"
            else:    
                n2d = str("%0.1fly"%dMatrix[hw][n2])
            row = [str(j+1), hw, str(planData[hw]['name']), n1d, n2d ]
        else:
            row = [str(j+1), 'unknown', 'na', 'na', 'na']
        if j == centerindex or j == centerindex+1:
            printLines.append(border)
            printLines.append(row)
        else:
            printLines.append(row)            
            
    
    # data = [['a', 'b', 'c'], ['aaaaaaaaaa', 'b', 'c'], ['a', 'bbbbbbbbbb', 'c']]
    # col_width = max(len(word) for row in data for word in row) + 2  # padding
    # for row in data:
    #     print "".join(word.ljust(col_width) for word in row)   
    
    cw = max( len(word) for row in printLines for word in row) + 2
    for row in printLines:
        print "".join(word.ljust(cw) for word in row)
    OUT=open("%s/02-HomeWorlds-NeighborDistances.txt" % (gameFolder), 'w')
    for row in printLines:
        OUT.write("".join(word.ljust(cw) for word in row))
        OUT.write("\n")
    OUT.close()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# 8. DUMP Location Table for likely homeworlds . . . . . . 
OUT=open("%s/02-HomeWorldLocations.txt" % (gameFolder), 'w')
OUT.write("ID\tNAME\tX\tY\tPlanet\n")
counter = 1
for id in homeWorlds:
    OUT.write("%d\t%s\t%s\t%s\t%s\t%s\n" % (counter, id, planData[id]['name'], planData[id]['x'], planData[id]['y'], planData[id]['HW'] ))
    counter += 1
OUT.close()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# 9. DUMP ALL MAP RESULTS FOR PLOTTING - - - - - - - - - - -  - - - - - -
OUT=open("%s/03-MapLocations.txt" % (gameFolder), 'w')
OUT.write("ID\tNAME\tX\tY\tHW\n")
for id in planData.iterkeys():
    if not id == 'unk':
        name = re.sub(r'[\s\'\-]', '', planData[id]['name'])
        OUT.write("%s\t%s\t%s\t%s\t%s\n" % (id, name, planData[id]['x'], planData[id]['y'], planData[id]['HW'] ))
OUT.close()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# 10. Run plotting script to generate starchart map  - - - - - - - - - - -  - - - - - -
if (plotMap == 1):
    args = "%s %s" % (gameData, gameName)
    runargz = args.split()
    # runargz.append(gameName)
    runlaunch = subprocess.Popen([Rwrapper, Rargs, ggplotR] + runargz )
    print("\n\nRunning STARCHART plot . . . \n%s %s %s %s\n\n" % (Rwrapper, Rargs, ggplotR, gameName))
    runlaunch.wait()
    print("Map output:  ./%s%sMapLocations.png" % (gameData, gameName))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
print "\n\n\n *  *  *  *  *      D O N E     *  *  *  *  **  \n\n"
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

