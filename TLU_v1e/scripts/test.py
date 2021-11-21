import matplotlib.pyplot as plt
import numpy as np
import matplotlib.mlab as mlab

print "TEST.py"
myFile= "./500ns_23ns.txt"

with open(myFile) as f:
    nsDeltas = map(float, f)

P= 1000000000 #display in ns
nsDeltas = [x * P for x in nsDeltas]
centerRange= 25
windowsns= 5
minRange= centerRange-windowsns
maxRange= centerRange+windowsns
plt.hist(nsDeltas, 60, range=[minRange, maxRange], facecolor='blue', align='mid', alpha= 0.75)
#plt.hist(nsDeltas, 100, normed=True, facecolor='blue', align='mid', alpha=0.75)
#plt.xlim((min(nsDeltas), max(nsDeltas)))
plt.xlabel('Time (ns)')
plt.ylabel('Entries')
plt.title('Histogram DeltaTime')
plt.grid(True)

#Superimpose Gauss
mean = np.mean(nsDeltas)
variance = np.var(nsDeltas)
sigma = np.sqrt(variance)
x = np.linspace(min(nsDeltas), max(nsDeltas), 100)
plt.plot(x, mlab.normpdf(x, mean, sigma))
print (mean, sigma)

#Display plot
plt.show()
