# OpenMeasurement initiative

The ad measurement market is witnessing an increasing demand from advertisers to deliver true “deduplicated” cross-media reach and frequency measurements. It is therefore, not far-fetched to start dreaming about the possibility of a universal, all-inclusive, reach and frequency deduplication report across all media where the advertising campaign has been aired. What is holding us back from achieving this dream? It is not easy to share viewership data.

Currently the ad viewership data is owned by the publishers. This means that the necessary first step to achieve true cross-media measurement is the ability to aggregate ad viewership data across multiple publishers. However, there are many technical, legal and incentive obstacles to achieve this. First, important and potentially sensitive information about individual users can be revealed in the joined data. In addition, publishers usually do not trust sharing their valuable viewership data among themselves for the risk of losing their share of the market, etc. The situation is even more complicated for larger companies, where the legalities concerning the user privacy, etc. makes the process of sharing ad viewership logs much more involved. As a result, the need for a privacy-preserving framework for the data collection of advertisement and consequent measurement across multiple parties is inevitable.


We aspire to provide the following
 * A completely open framework, to test, verify, and utilize by all the parties
 * A flexible methodology, to take into account the desired measurement quantities, advertising patterns, targetted audience, as well as the fundamental difference between different type of impressions.

## multi-dimensional frequency resolved measurement
The simplest example of a multi-dimensional measurement, is the complete frequency resolution between TV/linear and digital viewership. For an example, the following the the (n, m)-reach for the frequencies n for digital and m for linear for a typical report.

<img src="./img/2D_reach_synthetic_data.png" alt="synthetic" width="400"/>

using a virtual society mapping tailored for this report we can get a reach and frequency surface as follows

<img src="./img/2d_reach_VID_assignment.png" alt="VID_assignment" width="400"/>

## The virtual people, a generic model
Virtual people are fictitious IDs (numbers) that are possibly equipped with demographics and interests as well as the probability of exposure (activity) in each media. They match the total number as well as the statistical charactristics of the census, and their activities mimics the reach and frequency of the real advertising campaigns. It should not come as a surprise that a model of virtual people should either be almost exactly the actual people (leading exactly correct deduplicated reach and frequency if all people are observed) or is so generic that leads to large errors in measurement, therefor rendering it almost useless.


## The case dependent *virtual society*
A flexible methodology is only possible if a specific virtual society is tweaked and designed for each purpose separately. Virtual society is a dataframe of virtual individuals with equipped with certain demographics and/or interestes that have a tendency to receive advertisement thorough different media. This could be the tendency to generte specific cookie types in the case of digital advertising or the tendency to watch a specific network in the case of TV.

## Privacy as the key to multi-media measurement
The virtual society provides the first level of user privacy as the virtual users do not correspond to actual users, but they only follow the same  distribution as of the actual society. However, additional levels of privacy could also be combined with the virtual society approach. Thais means counting and frequency-aware sketches together with differentially private noises could be utilized after the virtual logs are created and before they are combined across different media, in order to reach the desired level of privacy for each

## Code structure and documentation
Please look at the documentation for the detailed structure of the code.
