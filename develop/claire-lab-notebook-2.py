
# coding: utf-8

# # Exploratory Data Analysis

# In[1]:

import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import seaborn as sns
from skimage.io import imread, imshow
from skimage import transform, img_as_float
import glob
import math
from importlib import reload


# ## Import utility functions and load data

# In[2]:

cwd = os.getcwd()
path = os.path.join(cwd, '..', 'src')
if not path in sys.path:
    sys.path.append(path)
import KaggleAmazonMain as kam


# In[3]:

reload(kam)


# In[42]:

#Load from pickle unless something has changed
X = pd.read_pickle('X.pkl')
y = pd.read_pickle('y.pkl')
X_sample, labels, names_train, tagged_df = kam.load_sample_training_data() #load sample data for plotting


# In[43]:

X.drop(['hough_skew','hough_kurtosis'], axis=1, inplace=True)


# In[44]:

X.head()


# In[45]:

y.head()


# In[46]:

print(X.shape, y.shape)


# ## Exploratory plots

# In[47]:

#Barplot of tag counts
get_ipython().magic('matplotlib inline')
def plot_sample_size(tagged_df):
    plt.rcParams['figure.figsize'] = (12, 5)
    print('There are {} unique tags in this data'.format(len(tagged_df.columns)))
    colors = cm.rainbow(np.linspace(0, 1, len(tagged_df.columns)))
    tagged_df.sum().sort_values(ascending=False).plot(title="Counts of Tags", color=colors, kind='bar')
    plt.show()
plot_sample_size(tagged_df)


# In[48]:

kam.plot_samples(X_sample, names_train, tagged_df, nrow=4, ncol=4)


# In[49]:

fig, axes = plt.subplots(1, 3, figsize=(10, 6))
axes[0].imshow(X_sample[1,:,:,0], cmap='Reds')
axes[1].imshow(X_sample[1,:,:,1], cmap='Greens')
axes[2].imshow(X_sample[1,:,:,2], cmap='Blues')


# In[50]:

plt.subplots_adjust(wspace=0, hspace=0)
for i in range(0,3):
    sample = np.random.randint(low=0, high=X_sample.shape[0]-1, size = 1)
    ind = names_train[sample[0]]
    tags = kam.get_labels(ind, tagged_df)
    kam.plot_rgb_dist(X_sample[sample[0],:,:,:],tags)


# Create features from the raw pixel data. These metrics should be metrics that describe patterns in the trends and distributions of the pixels. 
# Using binned historgram features to capture bimodality and general shape and location of distributions in red, green, and blue.
# 
# I want to try an ML algorithm with feature cdreation, and a NN with raw pixel data to compare results. 
# 
# binned mode differences is a feature created to discribe bimodal distributions. A lot of the r g b distributions are bimodal, which could offer interesting insight into the  classificatioin, so I created a feature to capture bimodal patterns in the r g b pixel distributions. The binned mode differences is simply the differnce between the two min bounds of the two largest count bins, or the two modes. If this value is large, then the two larges modes are a large distance from eachother, indicating the distribution is bimodal.

# In[51]:

#Binned mode differences
img=X_sample[2]
steps=np.arange(start=0,stop=1, step=.01)
kam.binned_mode_features_with_diagnostics(img, steps)


# Also created sobel features. blah blah blah about those

# In[52]:

from skimage.color import rgb2gray
from skimage import transform, img_as_float, filters
X_train_g = rgb2gray(X_sample)

X_train_sobel = []
for i in range(X_train_g.shape[0]):
    X_train_sobel.append(filters.sobel(X_train_g[i]))
X_train_sobel = np.asarray(X_train_sobel)


# In[53]:

kam.plot_samples(X_train_sobel, names_train, tagged_df, 4,4)


# Check out the features that were made... See if they describe separation of  classes. 

# In[54]:

sample_imgs_canny = kam.xform_to_canny(X_sample, sigma=.5)

kam.plot_samples(sample_imgs_canny, names_train, tagged_df, 4,4)


# In[55]:

#create table of each feature histograms for each label
X.set_index(y.index, inplace=True)
print(X.columns) #possible features to plot    
        
#plot_a_feature_by_labels('b_bimodal')        
kam.plot_a_feature_by_labels('sobel_colmean_std', X, y)


# # Random Forest

# ## Search random forest hyperparameter space

# In[ ]:

f2_scorer_obj = make_scorer(fbeta_score, beta=2, average='samples')

rf = RandomForestClassifier(bootstrap = True, 
                            oob_score = False,
                            n_jobs = -1,
                            random_state = 14113
                            )

parameters = {
    'n_estimators' : [100, 200, 300],
    'max_features' : ['sqrt', 'log2', 1, 2, 0.5, None],
    'class_weight' : ['balanced', 'balanced_subsample']
}

grid_search_obj = GridSearchCV(rf, parameters, scoring=f2_score, n_jobs=-1, cv=3)

grid_search_obj.fit(X_train, y_train)


# ### Persist grid search data -- *AS NEEDED*

# In[ ]:

grid_search_results = pd.DataFrame(grid_search.cv_results_)
grid_search_results.to_pickle('grid_search_results_df.pkl')

import pickle
pickle.dump(grid_search, open('grid_search_object.pkl', "wb"))


# ### Depersist grid search data -- *AS NEEDED*

# In[60]:

grid_search_results = pd.read_pickle('grid_search_results_df.pkl')


# In[64]:

grid_search_obj = pickle.load(open('grid_search_object.pkl', "rb"))


# ### Print 'best estimator'

# In[65]:

grid_search_obj.best_estimator_


# ## Fit Random Forest

# In[56]:

from sklearn.model_selection import train_test_split
X_train, X_validation, y_train, y_validation = train_test_split(X, y, test_size=0.40, random_state=14113)


# In[57]:

y.sum() #these are the sample sizes per class


# In[66]:

from sklearn.ensemble import RandomForestClassifier

rf = RandomForestClassifier(bootstrap=True, class_weight='balanced',
            criterion='gini', max_depth=None, max_features=None,
            max_leaf_nodes=None, min_impurity_split=1e-07,
            min_samples_leaf=1, min_samples_split=2,
            min_weight_fraction_leaf=0.0, n_estimators=300, n_jobs=-1,
            oob_score=False, random_state=14113, verbose=0,
            warm_start=False)


# In[67]:

rf.fit(X_train, y_train)


# In[17]:

# features ranking 

Feature_importance = pd.DataFrame(rf.feature_importances_, X_train.columns)
def plot_feature_importance(Feature_importance, n):
    '''
    plot top n features
    '''
    plt.rcParams['figure.figsize'] = (12, 5)
    Feature_importance = pd.DataFrame(rf.feature_importances_, X_train.columns)
    Feature_importance.columns = ['features']
    Feature_importance = Feature_importance.sort_values(by='features', axis=0, ascending=False)
    colors = cm.gist_heat(np.linspace(0, 1, len(tagged_df.columns)))
    Feature_importance.head(n).plot(title="Counts of Tags", color=colors, kind='bar')
    plt.show()

plot_feature_importance(Feature_importance, 10)


# ## F2-score and other metrics

# In[18]:

from sklearn.metrics import fbeta_score
probs = rf.predict_proba(X_validation)
predictions = kam.get_prediction_matrix(probs, 0.25)
predictions = rf.predict(X_validation)
score = fbeta_score(np.asarray(y_validation), predictions, beta=2, average='samples')
print('F2 score: ', score)


# precision is  of the imgaes taggd with a particular class, how many times that was the right class. 
# recall is of the images of a certain class, how many we correctly identified as that class. 
# f score is a blah average of precision and recall. 
# support is the same size of images with that label in the training data. 
# blah blah blah add descriptions of these metrics 

# In[19]:

#calc some other scoring metrics. precision, recall, and f1.
#The confusion matrix is diddicult to make and read for miltilabel classificatoin, but this table shows the same information 
#it shows the classes the model is perfomring well and poorly on.
from sklearn.metrics import precision_recall_fscore_support as score

precision, recall, fscore, support = score(y_validation, predictions)
Metrics = pd.DataFrame([precision, recall, support], index=['precision', 'recall', 'support'])
Metrics.columns = y_validation.columns
Metrics


# Trying to show recall increases with sample size, but its hard to see all the small sample points because they are so clustered. Basically, recall for sample size less than 2000 is generally poor, so we will focus on those samples.

# ## Diagnostics

# In[21]:

probs = rf.predict_proba(X_validation)


# ROC curves visualize performance of a class/binary classifier. Visualization of how predicted probabilities compare to the truth. 

# In[22]:

from sklearn import metrics

def plot_ROC(tag):
    '''
    plot ROC curve for a specific tag
    '''
    plt.rcParams['figure.figsize'] = (6,6)
    n = np.where(y_validation.columns==tag)[0][0]
    fpr, tpr, threshs = metrics.roc_curve(y_validation[tag], probs[n][:,1],
                                          pos_label=None, sample_weight=None, drop_intermediate=False)
    plt.figure()
    lw = 2
    plt.plot(fpr, tpr, color='darkorange',
             lw=lw)
    plt.plot([0, 1], [0, 1], color='navy', lw=lw, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(tag+'\nReceiver operating characteristic example')
    plt.legend(loc="lower right")
    plt.show()
    
plot_ROC('agriculture')
plot_ROC('bare_ground')


# In[23]:

def plot_decision_hist(tag):
    '''
    plots decision histograms with thresholds
    '''
    plt.rcParams['figure.figsize'] = (6,6)
    #Less than .5 is 0. greater is 1
    n = np.where(y_validation.columns==tag)[0][0]
    probs_df = pd.DataFrame(probs[n][:,1]).set_index(y_validation[tag])
    class0 =  np.array(probs_df.ix[0][0]) #0 does not have true tag
    class1 =  np.array(probs_df.ix[1][0]) #1 does have true tag

    S = class0
    # Histogram:
    # Bin it
    n, bin_edges = np.histogram(S, 30)
    # Normalize it, so that every bins value gives the probability of that bin
    bin_probability = n/float(n.sum())
    # Get the mid points of every bin
    bin_middles = (bin_edges[1:]+bin_edges[:-1])/2.
    # Compute the bin-width
    bin_width = bin_edges[1]-bin_edges[0]
    # Plot the histogram as a bar plot
    plt.bar(bin_middles, bin_probability, width=bin_width, color='red', alpha=.4)

    S = class1
    n, bin_edges = np.histogram(S, 30)
    bin_probability = n/float(n.sum())
    bin_middles = (bin_edges[1:]+bin_edges[:-1])/2.
    bin_width = bin_edges[1]-bin_edges[0]
    plt.bar(bin_middles, bin_probability, width=bin_width, color='green', alpha=.8)

    plt.axvline(x=0.5, color='k', linestyle='--')
    plt.title(tag+'\nScore distributions with splitting on a 0.5 threshold')
    plt.xlabel('Classification model score')
    plt.ylabel('Frequency')
    plt.show()
    
plot_decision_hist('agriculture')
plot_decision_hist('bare_ground')    


# Notice bare ground shows no separation at all, really. 

# # Oversampling

# The imbalanced-learn library imblearn has great modules for oversampling. WE are usign oeversampling because undersampling leads to loss of information, and some classes are very small so it would also lead to a very small dataset. Note oversampling can lead to overfitting the samller classes... Didn't work with multiclasses. I wrote my oen function for oversampling. It oversamples classes smaller than l up to size l by repeating a relabeled image the same as the randomly sampled image. 

# In[45]:

#randomly over sample

def over_sample(X, y, l):
    '''
    resamples classes smaller than l to be size l
    '''
    y_upsampled=y.copy()
    X_upsampled=X.copy()
    cols=y.sum()[y.sum()<l].index #classes with less than l samples.
    for c in cols:
        I_y = y[y[c]==1].sample(n=l-y[c].sum(), replace=True)
        x_index = I_y.index #index of image names
        I_y.reset_index(drop=True, inplace=True) #rename y index
        y_upsampled = y_upsampled.append(I_y, )
        
        I_x = X.loc[x_index]
        I_x.reset_index(drop=True, inplace=True) #rename y index
        X_upsampled = X_upsampled.append(I_x, )

    return X_upsampled, y_upsampled

X_train, X_validation, y_train, y_validation = train_test_split(X, y, test_size=0.40, random_state=14113)
X_upsampled, y_upsampled = over_sample(X=X_train, y=y_train, l=10000)


# In[46]:

y_upsampled.sum()


# In[47]:

from sklearn.ensemble import RandomForestClassifier

rf = RandomForestClassifier(n_estimators = 300, 
                            max_features = 'sqrt',
                            bootstrap = True, 
                            oob_score = False,
                            n_jobs = -1,
                            random_state = 14113,
                            class_weight = 'balanced')

rf.fit(X_upsampled, y_upsampled)


# In[48]:

from sklearn.metrics import fbeta_score

probs = rf.predict_proba(X_validation)
predictions = kam.get_prediction_matrix(probs, 0.25)

score = fbeta_score(np.asarray(y_validation), predictions, beta=2, average='samples')

print('F2 score: ', score)


# In[57]:

from sklearn.ensemble import ExtraTreesClassifier


# In[58]:

et = ExtraTreesClassifier(n_estimators = 300,
                          n_jobs = -1,
                          random_state = 14113,
                          class_weight = 'balanced')

et.fit(X_upsampled, y_upsampled)


# In[59]:

probs = et.predict_proba(X_validation)
predictions = kam.get_prediction_matrix(probs, 0.25)

score = fbeta_score(np.asarray(y_validation), predictions, beta=2, average='samples')

print('F2 score: ', score)


# In[60]:

from sklearn.ensemble import AdaBoostClassifier


# In[63]:

ab = AdaBoostClassifier(random_state = 14113)

ab.fit(X_upsampled, y_upsampled)


# In[ ]:




# In[27]:

from sklearn.metrics import fbeta_score

predictions = rf.predict(X_validation)
fbeta_score(np.asarray(y_validation), predictions, beta=2, average='samples')


# In[49]:

from sklearn.metrics import precision_recall_fscore_support as score

precision, recall, fscore, support = score(y_validation, predictions)
Metrics = pd.DataFrame([precision, recall, support], index=['precision', 'recall', 'support'])
Metrics.columns = y_validation.columns
Metrics


# # LR model for smaller classes
# I want to try some logistic regression models for the classes that are performing poorly. These are all the classes with smaller sampling sizes. These classes will be removed from the RF. Try RF witout them and see if it changes performance. Also try binary RF classifyer on the smallers. See if LR is better. 
# 
# Start with bare_ground example, since we have seen its poor performance in the RF. 

# In[29]:

#Perform LR on these classes. 
l=2000
cols=y.sum()[y.sum()<l].index
cols


# Adding a 10-fold cv cause it is needed for LR model. So bootstrapping like the RF

# In[ ]:

#Lin reg model
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

lr = LogisticRegression(random_state=1, class_weight='balanced')
# 10-Fold Cross Validation
scores = cross_val_score(lr, X_upsampled, y_upsampled['bare_ground'], cv=10)

np.set_printoptions(precision=8)
print("cross validation scores {}".format(scores)) #the cross_val_score uses the default scoring method from the RF, which is oob error. 
print("Average cross validation accuracy scores: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))


# In[31]:

#Metrics and distrubtion plot
lr.fit(X_upsampled, y_upsampled['bare_ground'])
pred_lr = lr.predict(X_validation)
coef_lr = lr.coef_.ravel()
print("Training accuracy is: {}".format(lr.score(X_upsampled, y_upsampled['bare_ground'])))
print('{} percent of the feature have been removed by setting the coefficents to 0'.format((np.mean(coef_lr == 0)*100).round(2)))


# In[147]:

from sklearn.metrics import fbeta_score
print("The new f2 score for this class is: {}".format(fbeta_score(np.asarray(y_validation['bare_ground']), pred_lr, beta=2))) #This is the score now... 
n = np.where(y_validation.columns== 'bare_ground')[0][0]
print("The f2 score from the multiclass RF is: {}".format(fbeta_score(np.asarray(y_validation['bare_ground']), predictions[:,n], beta=2))) #but this is what it was before


# In[57]:

# try a RF
#RF for larger classes
rf = RandomForestClassifier(n_estimators = 100, 
                            max_features = 'sqrt',
                            bootstrap = True, 
                            oob_score = True,
                            n_jobs = -1,
                            random_state = 14113,
                            class_weight = 'balanced_subsample')

rf.fit(X_upsampled, y_upsampled['bare_ground'])
print('The oob error for this random forest is {}'.format(rf.oob_score_.round(5)))


preds_rf = rf.predict(X_validation)
print("this F2 score is : {}".format(fbeta_score(np.asarray(y_validation['bare_ground']), preds_rf, beta=2)))


# In[ ]:

print("The new f2 score for this class is: {}".format(fbeta_score(np.asarray(y_validation['bare_ground']), preds_rf, beta=2))) #This is the score now... 
n = np.where(y_validation.columns== 'bare_ground')[0][0]
print("The f2 score from the multiclass RF is: {}".format(fbeta_score(np.asarray(y_validation['bare_ground']), predictions[:,n], beta=2))) #but this is what it was before


# In[116]:

from sklearn.metrics import precision_recall_fscore_support as score

precision, recall, fscore, support = score(y_validation['bare_ground'], pred_lr)
Metrics = pd.DataFrame([precision, recall, support], index=['precision', 'recall', 'support'])
Metrics #wow precision is horrible


# In[148]:


def micro_model_dist_plot(tag, probs):
    '''
    plots decision histograms with thresholds
    '''
    plt.rcParams['figure.figsize'] = (6,6)
    #Less than .5 is 0. greater is 1
    n = np.where(y_validation.columns==tag)[0][0]
    probs_df = pd.DataFrame(probs).set_index(y_validation[tag])
    class0 =  np.array(probs_df.ix[0][0]) #0 does not have true tag
    class1 =  np.array(probs_df.ix[1][0]) #1 does have true tag

    S = class0
    # Histogram:
    # Bin it
    n, bin_edges = np.histogram(S, 30)
    # Normalize it, so that every bins value gives the probability of that bin
    bin_probability = n/float(n.sum())
    # Get the mid points of every bin
    bin_middles = (bin_edges[1:]+bin_edges[:-1])/2.
    # Compute the bin-width
    bin_width = bin_edges[1]-bin_edges[0]
    # Plot the histogram as a bar plot
    plt.bar(bin_middles, bin_probability, width=bin_width, color='red', alpha=.4)

    S = class1
    n, bin_edges = np.histogram(S, 30)
    bin_probability = n/float(n.sum())
    bin_middles = (bin_edges[1:]+bin_edges[:-1])/2.
    bin_width = bin_edges[1]-bin_edges[0]
    plt.bar(bin_middles, bin_probability, width=bin_width, color='green', alpha=.8)

    plt.axvline(x=0.5, color='k', linestyle='--')
    plt.title(tag+'\nScore distributions with splitting on a 0.5 threshold')
    plt.xlabel('Classification model score')
    plt.ylabel('Frequency')
    plt.show()
    
probs = lr.predict_proba(X_validation)
tag='bare_ground'
micro_model_dist_plot(tag, probs)


# # Put it all together

# In[ ]:

#pick threshold. 
#function to find optimal threshold for recall
#Adam might have this written already
#Just use .5 threshold for now. 


# In[ ]:

#Ensemble all models together

#Big model

#Mini Models


# In[50]:

#The smaller classes will use a LR model
l=2000
cols_small=y.sum()[y.sum()<l].index
cols_large=y.sum()[y.sum()>=l].index


# In[51]:

X_train, X_validation, y_train, y_validation = train_test_split(X, y, test_size=0.40, random_state=14113)
X_upsampled, y_upsampled = over_sample(X=X_train, y=y_train, l=10000)

#Same x is used. Need different ys
y_train_mini = y_upsampled[cols_small]
y_train_large = y_upsampled[cols_large]
y_validation_mini = y_validation[cols_small]
y_validation_large = y_validation[cols_large]


# In[52]:

#RF for larger classes
rf = RandomForestClassifier(n_estimators = 100, 
                            max_features = 'sqrt',
                            bootstrap = True, 
                            oob_score = True,
                            n_jobs = -1,
                            random_state = 14113,
                            class_weight = 'balanced_subsample')

rf.fit(X_upsampled, y_train_large)
print('The oob error for this random forest is {}'.format(rf.oob_score_.round(5)))


predictions = rf.predict(X_validation)
print("this F2 score is : {}".format(fbeta_score(np.asarray(y_validation_large), predictions, beta=2, average='samples')))


# In[53]:

# LR for all smaller classes
from sklearn.linear_model import LogisticRegression
def mini_models(cols_small):
    df = pd.DataFrame()
    for c in cols_small:
        lr = LogisticRegression(random_state=1, class_weight='balanced')
        lr.fit(X_upsampled, y_train_mini[c])
        pred_lr = lr.predict(X_validation)
        df[c] = pred_lr
    return df
preds_mini = mini_models(cols_small)


# In[54]:

#put RF scores and LR scores together
preds_large = pd.DataFrame(predictions)
preds_large.columns=cols_large
preds_all = pd.concat([preds_large, preds_mini], axis=1, join_axes=[preds_large.index])
y_validation_all = pd.concat([y_validation[cols_large], y_validation[cols_small]], axis=1, join_axes=[y_validation.index])


precision, recall, fscore, support = score(y_validation_all, preds_all)
Metrics = pd.DataFrame([precision, recall, support], index=['precision', 'recall', 'support'])
Metrics.columns = y_validation_all.columns
Metrics


# In[56]:

#calc F2 score from that. 
print("this F2 score for this weird ensemble method is : {}".format(
    fbeta_score(np.asarray(y_validation_all), preds_all, beta=2, average='samples')))


# In[ ]:



