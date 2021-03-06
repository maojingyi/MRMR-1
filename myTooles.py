import numpy as np
from sklearn.model_selection import train_test_split
from scipy.stats.stats import pearsonr
from sklearn import svm
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import roc_auc_score
from sklearn.metrics import accuracy_score
from sklearn.metrics import matthews_corrcoef
from sklearn.svm import SVC
def loadData(dataFileName):
	inputMatrix = np.loadtxt(open(dataFileName,'rb'), delimiter=",", skiprows=1)  
	return inputMatrix

def preProcessing(inputMatrix):
	arrayInput = np.array(inputMatrix)
	numSample, numFeature = arrayInput.shape
	numFeature = numFeature-1
	labelArray = arrayInput[:,-1]
	featureArray = arrayInput[:, 0:numFeature]
	return labelArray, featureArray

def getPosNegIdx(label):
	posIdx = []
	negIdx = []
	for i in range(0, len(label)):
		if label[i]==0:
			negIdx.append(i)
		else:
			posIdx.append(i)
	return posIdx, negIdx

def selectOneFeature(featureIndex, featureSpace):
#	print featureIndex
	return featureSpace[:,featureIndex]

#compute the F-static on featureIdx
def getfStatis(featureIdx, X_train, posIdx, negIdx):
	featureSelectedi = selectOneFeature(featureIdx, X_train)
	nPos = len(posIdx)
	nNeg = len(negIdx)
	sigmaSQPos = np.var(featureSelectedi[posIdx])
	sigmaSQPos = np.asarray(sigmaSQPos)
	sigmaSQNeg = np.var(featureSelectedi[negIdx])
	sigmaSQNeg = np.asarray(sigmaSQNeg)
	nPosArray = np.asarray(nPos)
	nNegArray = np.asarray(nNeg)
	sigmaSQ = [(nPosArray-1)*sigmaSQPos+(nNegArray-1)*sigmaSQNeg]/(nPosArray+nNegArray-2)
	gMean = np.mean(featureSelectedi)
	gPosMean = np.mean(featureSelectedi[posIdx])
	gNegMean = np.mean(featureSelectedi[negIdx])
#	outputTest.write("gPosMean = %f, gMean = %f, gNegMean = %f, sigmaSQ = %f\n"% (gPosMean, gMean, gNegMean, sigmaSQ))
	if sigmaSQ == 0:
		fStatis = 0
	else:
		fStatis = [nPosArray*(gPosMean-gMean)*(gPosMean-gMean)+nNegArray*(gNegMean-gMean)*(gNegMean-gMean)]/(sigmaSQ)
#	print fStatis
	return fStatis

def findFirstFeature(trainFStatis):
	#just use the maxF-statis as the first feature
	return trainFStatis.argmax()

def getTrainFStatis(featureTrainNum, X_train, posIdx, negIdx):
	for i in range(0, featureTrainNum):
		trainFStatis[i] = getfStatis(i, X_train, posIdx, negIdx)
	return trainFStatis

#judege the feature, if all the element in one feature is the same, it will return 1
#bad feature means all the element in the feature are the same
def judgeBadFeature(feature):
	meanValue = np.mean(feature)
#	print meanValue
	judgeArray = np.zeros(len(feature))
	for i in range(len(feature)):
		judgeArray[i] = meanValue 
	return (feature==judgeArray).all()

def evaluate_binary_predictions(true_y, pred_scores):
    auc = roc_auc_score(true_y, pred_scores)
    acc = accuracy_score(true_y, pred_scores)  # using default cutoff of 0.5
    mcc = matthews_corrcoef(true_y, pred_scores)
    return auc, mcc, acc
    

#report warning when all of the one feature is 0 
def FCDMethodOnI(featureIdxi, X_train, trainFStatis, seletedFeature):
	featureSelectedi = selectOneFeature(featureIdxi, X_train)
	numSeletedFeature = len(seletedFeature)
	sumAllPCC = 0
	if (judgeBadFeature(selectOneFeature(featureIdxi, X_train)) == 1):
		return -1
	else:
		for featureIdxj in seletedFeature:
			sumAllPCC += abs(pearsonr(selectOneFeature(featureIdxi, X_train), selectOneFeature(featureIdxj, X_train))[0])
#		print pearsonr(selectOneFeature(featureIdxi, X_train), selectOneFeature(featureIdxj, X_train))
		sumAllPCC = sumAllPCC/numSeletedFeature
	return trainFStatis[featureIdxi]-sumAllPCC

def FCQMethodOnI(featureIdxi, X_train, trainFStatis, seletedFeature):
#	print featureIdxi
#	print seletedFeature
	featureSelectedi = selectOneFeature(featureIdxi, X_train)
	numSeletedFeature = len(seletedFeature)
	sumAllPCC = 0
	if (judgeBadFeature(selectOneFeature(featureIdxi, X_train)) == 1):
		return -1
	else:
		for featureIdxj in seletedFeature:
			sumAllPCC += abs(pearsonr(selectOneFeature(featureIdxi, X_train), selectOneFeature(featureIdxj, X_train))[0])
		sumAllPCC = sumAllPCC/numSeletedFeature
	return trainFStatis[featureIdxi]/sumAllPCC

#use FCD method to find the next feature
#FCDSelectFeature [1 2 3]
#the selected feature is FCDSelectFeature.argmax
def FCDmethodFindFeature(omegaFeature, X_train, trainFStatis, seletedFeature):
	FCDSelectFeature = np.zeros(len(omegaFeature)+len(seletedFeature))
	for featureInOmega in omegaFeature:
#		print featureInOmega
		FCDSelectFeature[featureInOmega] = FCDMethodOnI(featureInOmega, X_train, trainFStatis, seletedFeature)
#	outputTest.write("%f"%(FCDSelectFeature))
	np.savetxt("testOut.txt",FCDSelectFeature, fmt="%f",delimiter=",")
	return FCDSelectFeature.argmax()

def FCQmethodFindFeature(omegaFeature, X_train, trainFStatis, seletedFeature):
	FCQSelectFeature = np.zeros(len(omegaFeature)+len(seletedFeature))
	for featureInOmega in omegaFeature:
#		print featureInOmega
		FCQSelectFeature[featureInOmega] = FCQMethodOnI(featureInOmega, X_train, trainFStatis, seletedFeature)
#	outputTest.write("%f"%(FCQSelectFeature))
	np.savetxt("testOut.txt",FCQSelectFeature, fmt="%f",delimiter=",")
	return FCQSelectFeature.argmax()

#toSelectNum is the hyper parameter to choose the number of selection
#methodPara = 1 choose FCD method
#methodPara = 2 choose FCQ method
def MRMRmethod(toSelectNum, methodPara, seletedFeature):
	firstFeature = findFirstFeature(trainFStatis)
	seletedFeature.add(firstFeature)
	#omegaFeature are the unseleted feature set
	omegaFeature = setUniversalSet-seletedFeature
	nextFeature = FCDmethodFindFeature(omegaFeature, X_train, trainFStatis, seletedFeature)
	for i in range(0, toSelectNum):
		seletedFeature.add(nextFeature)
#		print seletedFeature
		omegaFeature = setUniversalSet-seletedFeature
		if methodPara == 1:
			nextFeature = FCDmethodFindFeature(omegaFeature, X_train, trainFStatis, seletedFeature)
		elif methodPara == 2:
			nextFeature = FCQmethodFindFeature(omegaFeature, X_train, trainFStatis, seletedFeature)
#		print seletedFeature
	return seletedFeature

def crossValidation(featureArray, labelArray, test_size):
	X_train, X_test, y_train, y_test = train_test_split(featureArray, labelArray, test_size=0.2, random_state=42)
	return X_train, X_test, y_train, y_test

def selectAndTrain(toSelectNum, selectMethod):
	seletedFeature = set()
	methodSelectedFeature = MRMRmethod(toSelectNum, selectMethod, seletedFeature)
	listMethodSelectedFeature = list(methodSelectedFeature)
	SVMmodel = SVC()
	SVMmodel.fit(X_train[:, listMethodSelectedFeature], y_train)
	y_Pred = SVMmodel.predict(X_test[:, listMethodSelectedFeature])
	score = evaluate_binary_predictions(y_test,y_Pred)
	outputTest.write("toSelectNum = %d, selectMethod = %d, selectedAUC = %f, selectedMCC = %f, selectedACC = %f\n"%(toSelectNum, selectMethod, score[0], score[1], score[2]))
	return 0

def withoutMRMR(X_train, y_train, X_test, y_test):
	SVMmodel = SVC()
	SVMmodel.fit(X_train, y_train)
	y_Pred = SVMmodel.predict(X_test)
	score = evaluate_binary_predictions(y_test,y_Pred)
	outputTest.write("toSelectNum = 0, selectMethod = 0, selectedAUC = %f, selectedMCC = %f, selectedACC = %f\n"%(score[0], score[1], score[2]))
	return 0

crossValRatio = 0.2
toSelectNum = 50
selectMethod = 1
#load the data, get the features and label
dataFileName = "data/data.csv"
inputMatrix = loadData(dataFileName)
labelArray, featureArray = preProcessing(inputMatrix)
#split the data
X_train, X_test, y_train, y_test = crossValidation(featureArray, labelArray, crossValRatio)
sampleTrainNum, featureTrainNum = X_train.shape
posIdx, negIdx = getPosNegIdx(y_train)
#f(i, h) = featureSelectedi, c(i,j) = PCCij
#print getfStatis(featureIdxi, X_train, posIdx, negIdx)
#print PCCij
outputTest = open("outputTest.txt", "w")
#featureSelectedi = selectOneFeature(featureIdxi, X_train)
withoutMRMR(X_train, y_train, X_test, y_test)
trainFStatis = np.zeros(featureTrainNum)
setUniversalSet = {x for x in range(featureTrainNum)}
trainFStatis = getTrainFStatis(featureTrainNum, X_train, posIdx, negIdx)
print sampleTrainNum
#testParaNum = range(50, sampleTrainNum, 50)
testParaNum = range(20, sampleTrainNum, 10)
#testParaNum = range(1, 3, 1)
testMethodNum = range(1,3)
for j in testMethodNum:
	for i in testParaNum:
		print i
		selectAndTrain(i, j)







#outputTest.write("toSelectNum = %d, selectMethod = %d, selectedAUC = %f, selectedMCC = %f, selectedACC = %f\n"%(toSelectNum, selectMethod, score[0], score[1], score[2]))
#print("selectedAUC:", score[0])
#print("selectedMCC:", score[1])
#print("selectedACC:", score[2])
'''
trainFStatis = np.zeros(featureTrainNum)
seletedFeature = set()
setUniversalSet = {x for x in range(featureTrainNum)}
trainFStatis = getTrainFStatis(featureTrainNum, X_train, posIdx, negIdx)
methodSelectedFeature = MRMRmethod(toSelectNum, selectMethod)
listMethodSelectedFeature = list(methodSelectedFeature)
SVMmodel = SVC()
SVMmodel.fit(X_train[:, listMethodSelectedFeature], y_train)
y_Pred = SVMmodel.predict(X_test[:, listMethodSelectedFeature])
score = evaluate_binary_predictions(y_test,y_Pred)
SVMmodelOri = SVC()
SVMmodelOri.fit(X_train, y_train)
y_PredOri = SVMmodelOri.predict(X_test)
scoreOri = evaluate_binary_predictions(y_test,y_PredOri)
print("AUC:", scoreOri[0])
print("MCC:", scoreOri[1])
print("ACC:", scoreOri[2])
'''

