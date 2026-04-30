import numpy as np
from scipy.interpolate import interp1d

# 1. Your raw, sparse coordinates
raw_data = """
1       -0.000576
0.975    0.005328
0.95     0.010368
0.925    0.014688
0.9      0.01836
0.875    0.0216
0.85     0.024264
0.825    0.02664
0.8      0.028656
0.775    0.030384
0.75     0.031824
0.725    0.03312
0.7      0.034272
0.675    0.035208
0.65     0.036072
0.625    0.036792
0.6      0.037368
0.575    0.037944
0.55     0.038376
0.5      0.039096
0.45     0.039456
0.4      0.0396
0.35     0.039384
0.3      0.03888
0.25     0.038016
0.2      0.036504
0.175    0.035496
0.15     0.034272
0.125    0.03276
0.1      0.030816
0.075    0.028368
0.05     0.024984
0.0375   0.022752
0.025    0.019872
0.0125   0.01548
0.0075   0.012672
0        0
0.0075  -0.012672
0.0125  -0.015552
0.025   -0.020232
0.0375  -0.023328
0.05    -0.025776
0.075   -0.029376
0.1     -0.031968
0.125   -0.033984
0.15    -0.035496
0.175   -0.03672
0.2     -0.037584
0.25    -0.03888
0.3     -0.039456
0.35    -0.039528
0.4     -0.038952
0.45    -0.037728
0.5     -0.035784
0.55    -0.03276
0.575   -0.030672
0.6     -0.028008
0.625   -0.024624
0.65    -0.020304
0.675   -0.01548
0.7     -0.010728
0.725   -0.00648
0.75    -0.002592
0.775    0.000864
0.8      0.003816
0.825    0.006336
0.85     0.008208
0.875    0.009504
0.9      0.009936
0.925    0.009432
0.95     0.007632
0.975    0.00432
1       -0.000936
1       -0.000576
"""

# Parse the text into a numpy array
lines = raw_data.strip().split('\n')
points = np.array([list(map(float, line.split())) for line in lines])

# 2. Find the Leading Edge (where X = 0) to split Top and Bottom
le_index = np.argmin(points[:, 0])

top_points = points[:le_index+1]
bot_points = points[le_index:]

# scipy's interp1d requires strictly increasing X values.
# Top points go from 1 down to 0, so we reverse them.
top_x = top_points[::-1, 0]
top_z = top_points[::-1, 1]

# Bottom points go from 0 to 1, but we must remove exact duplicate X values (like your last 2 lines)
bot_x, unique_indices = np.unique(bot_points[:, 0], return_index=True)
bot_z = bot_points[unique_indices, 1]

# 3. Create the mathematical splines
f_top = interp1d(top_x, top_z, kind='cubic')
f_bot = interp1d(bot_x, bot_z, kind='cubic')

# 4. Generate 150 points per surface using COSINE SPACING
# This mathematically clusters points heavily at x=0 and x=1
N_per_surface = 150
beta = np.linspace(0, np.pi, N_per_surface)
x_dense = 0.5 * (1.0 - np.cos(beta))

# 5. Evaluate the smooth Z coordinates
z_top_dense = f_top(x_dense)
z_bot_dense = f_bot(x_dense)

# 6. Reassemble the airfoil (Top surface goes from 1 down to 0)
top_x_final = x_dense[::-1]
top_z_final = z_top_dense[::-1]

# Bottom surface goes from 0 up to 1 (skip the first point so LE doesn't duplicate)
bot_x_final = x_dense[1:]
bot_z_final = z_bot_dense[1:]

final_x = np.concatenate((top_x_final, bot_x_final))
final_z = np.concatenate((top_z_final, bot_z_final))

# 7. Write the new high-density airfoil to a text file
output_filename = "trial_airfoil_dense.txt"
with open(output_filename, "w") as f:
    for x, z in zip(final_x, final_z):
        f.write(f"{x:.6f}  {z:.6f}\n")

print(f"✅ Success! Saved {len(final_x)} perfectly spaced points to {output_filename}")