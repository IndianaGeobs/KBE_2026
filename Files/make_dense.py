import numpy as np
from scipy.interpolate import interp1d

# 1. Your raw, sparse coordinates
raw_data = """
1.000000  0.000000
  0.997260  0.000430
  0.989070  0.001690
  0.975530  0.003770
  0.956770  0.006590
  0.933010  0.010090
  0.904510  0.014160
  0.871570  0.018700
  0.834570  0.023570
  0.793890  0.028640
  0.750000  0.033770
  0.703370  0.038800
  0.654510  0.043590
  0.603960  0.048000
  0.552260  0.051890
  0.500000  0.055140
  0.447740  0.057630
  0.396040  0.059280
  0.345490  0.060000
  0.296630  0.059750
  0.250000  0.058490
  0.206110  0.056210
  0.165440  0.052940
  0.128430  0.048710
  0.095490  0.043590
  0.066990  0.037660
  0.043230  0.031020
  0.024470  0.023800
  0.010930  0.016120
  0.002740  0.008140
  0.000000  0.000000
  0.002740 -0.008140
  0.010930 -0.016120
  0.024470 -0.023800
  0.043230 -0.031020
  0.066990 -0.037660
  0.095490 -0.043590
  0.128430 -0.048710
  0.165430 -0.052940
  0.206110 -0.056210
  0.250000 -0.058490
  0.296630 -0.059750
  0.345490 -0.060000
  0.396040 -0.059280
  0.447740 -0.057630
  0.500000 -0.055140
  0.552260 -0.051890
  0.603960 -0.048000
  0.654510 -0.043590
  0.703370 -0.038800
  0.750000 -0.033770
  0.793890 -0.028640
  0.834560 -0.023570
  0.871570 -0.018700
  0.904510 -0.014160
  0.933010 -0.010090
  0.956770 -0.006590
  0.975530 -0.003770
  0.989070 -0.001690
  0.997260 -0.000430
  1.000000  0.000000
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
output_filename = "hor_tail_dense.txt"
with open(output_filename, "w") as f:
    for x, z in zip(final_x, final_z):
        f.write(f"{x:.6f}  {z:.6f}\n")

print(f"✅ Success! Saved {len(final_x)} perfectly spaced points to {output_filename}")