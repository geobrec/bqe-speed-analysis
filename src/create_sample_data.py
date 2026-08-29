import numpy as np                                  # numerical arrays and random numbers
import pandas as pd                                 # dataframes

rng = np.random.default_rng(42)                     # seeded generator — same "random" data every run

# --- build the time axis -------------------------------------------------
idx = pd.date_range(                                # a regular sequence of timestamps
    "2023-01-01",                                   # start
    "2023-12-31 23:55",                             # end
    freq="5min",                                    # one row every 5 minutes
    tz="America/New_York",                          # timezone-aware from the start
)
hour = idx.hour + idx.minute / 60                   # hour as a decimal, e.g. 8.5 for 08:30
dow = idx.dayofweek                                 # 0 = Monday ... 6 = Sunday

# --- build a realistic speed signal --------------------------------------
free_flow = 68.0                                    # speed when nothing is wrong, mph
am = 14 * np.exp(-0.5 * ((hour - 7.75) / 1.1) ** 2) # Gaussian dip centred on 07:45
pm = 18 * np.exp(-0.5 * ((hour - 17.25) / 1.4) ** 2)# deeper, wider dip centred on 17:15
peak_drop = np.where(dow < 5, am + pm, 0.35 * (am + pm))  # weekdays full peaks, weekends 35%

speed = free_flow - peak_drop + rng.normal(0, 2.5, len(idx))  # subtract peaks, add 2.5 mph noise

# --- inject incidents: sharp multi-interval drops ------------------------
for start in rng.choice(len(idx) - 12, size=40, replace=False):  # 40 random start points
    speed[start:start + rng.integers(3, 12)] -= rng.uniform(20, 35)  # drop 20-35 mph for 3-12 intervals

df = pd.DataFrame({                                 # assemble into a table
    "timestamp": idx,
    "speed_mph": speed,
    "segment_id": "BQE-0231",
})

# --- inject the defects real sensor data actually has --------------------
df.loc[rng.choice(len(df), 300, replace=False), "speed_mph"] = np.nan  # dropouts
df.loc[rng.choice(len(df), 25, replace=False), "speed_mph"] = 0.0      # stuck-at-zero sensor
df.loc[rng.choice(len(df), 15, replace=False), "speed_mph"] = 255.0    # vendor error code
df = df.drop(index=rng.choice(len(df), 200, replace=False))            # missing rows = time gaps
df = pd.concat([df, df.sample(50, random_state=1)])                    # duplicate timestamps

df.sample(frac=1, random_state=2).to_csv(           # shuffle row order (real exports aren't sorted)
    "data/raw/speeds_synthetic.csv", index=False    # index=False → don't write the row numbers
)
print(f"wrote {len(df):,} rows")                    # f-string; :, adds thousands separators