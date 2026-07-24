import pandas as pd

# Đọc danh sách doanh nghiệp
df = pd.read_csv("data/listed_companies.csv")

# Chuẩn hóa schema nếu file master data mới dùng cột từ vnstock
rename_map = {
    "symbol": "ticker",
    "organ_name": "name",
    "exchange": "market",
}
df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

for column in ["ticker", "name", "market", "sector"]:
    if column not in df.columns:
        df[column] = ""

# Chuẩn hóa tên sàn
df["market"] = (
    df["market"].astype(str).str.upper().replace(
        {
            "HSX": "HOSE",
            "HOSE": "HOSE",
            "HNX": "HNX",
            "UPCOM": "UPCOM",
            "UPCOMINDEX": "UPCOM",
        }
    )
)

# Chọn theo tỷ lệ
hose = df[df["market"] == "HOSE"].head(70)
hnx = df[df["market"] == "HNX"].head(20)
upcom = df[df["market"] == "UPCOM"].head(10)

# Ghép lại
universe = pd.concat([hose, hnx, upcom], ignore_index=True)

# Thêm metadata
universe["version"] = "v1"
universe["effective_date"] = "2026-07-19"

# Chỉ giữ các cột cần thiết
universe = universe[
    [
        "ticker",
        "name",
        "market",
        "sector",
        "version",
        "effective_date",
    ]
]

# Xuất file
universe.to_csv(
    "universe/ticker_universe_v1.csv",
    index=False,
    encoding="utf-8-sig"
)

print("=" * 40)
print(f"HOSE : {len(hose)}")
print(f"HNX  : {len(hnx)}")
print(f"UPCOM: {len(upcom)}")
print("=" * 40)
print(f"TOTAL: {len(universe)}")
print("Saved -> universe/ticker_universe_v1.csv")
