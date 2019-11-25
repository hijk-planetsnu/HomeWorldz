#!/usr/bin/env Rscript
# --------------------------------------------------------------
# Planet Map Locations . . . . 
# --------------------------------------------------------------
rm(list=ls())
argsIN = commandArgs(trailingOnly=TRUE)
library(ggplot2)

gameFolder = "001-GameData/"
gameName = "295020-BIRD-034/"

if (length(argsIN) > 1) {
	gameFolder = as.character(argsIN[1])
	gameName = as.character(argsIN[2])
}

data <- as.data.frame(read.table(paste(gameFolder, gameName,'03-MapLocations.txt',sep=""),sep='\t',header=T))
#summary(data)
data$HW <- as.factor(data$HW)
data$HW <- factor(data$HW, levels = c('no', 'possible', 'StarBase', 'HomeWorld' ))

data$pointSize <- c("1")
data$pointSize[which(data$HW == 'possible')] <- c("3")
data$pointSize[which(data$HW == 'StarBase')] <- c("5")
data$pointSize[which(data$HW == 'HomeWorld')] <- c("6")

data$ID <- as.character(data$ID)
data$planLabels <- data$ID
data$planLabels[data$HW == 'no'] <- c(" ")

hwxy <- data[data$HW=="HomeWorld",]


p <- ggplot(data,aes(x=X,y=Y,group=HW, size=pointSize)) +
	#geom_point(data=hwxy, aes(x=X,y=Y), shape=1, colour="grey30", size=20) +
	annotate("path", x=hwxy$X+450*cos(seq(0,2*pi,length.out=100)), y=hwxy$Y+450*sin(seq(0,2*pi,length.out=100)), colour="#9d64cc") +
	geom_point(aes(colour=HW, size=pointSize),  alpha=0.75) +
	scale_size_manual(values = c(1.5,4,5,6), guide=FALSE) +
 	scale_x_continuous("") +
 	scale_y_continuous("") +
 	guides(colour = guide_legend(override.aes = list(size=6))) +
 	geom_text(aes(label=planLabels, colour=HW), hjust=1.2, vjust=1.2, show.legend=FALSE) + 
 	scale_colour_discrete("Home Worlds", l=40, labels=c("no", "possible", "likely", "HomeWorld")) +
 	#scale_colour_brewer(palette="Dark2",name="Planets:", labels=c('HomeWorld', 'no', 'possible', 'StarBase' )) + 	
 	labs(title=paste(gameName, ": Possible Home Worlds")) +
    theme(legend.position=c(0.9,0.9), legend.title=element_text(size=12,face="bold"), legend.text=element_text(size=12)) +
	theme(axis.text.x=element_text(size=12,color="gray30")) +
	theme(axis.text.y=element_text(size=12,color="gray30")) +
	theme(axis.title.x=element_text(size=14)) +
	theme(axis.title.y=element_text(size=14)) +
	theme(plot.title=element_text(size=14))
p

ggsave(file=paste(gameFolder, gameName,'04-MapLocations.png',sep=""),dpi=300)





