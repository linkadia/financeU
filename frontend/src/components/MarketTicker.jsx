import { Box, Typography } from "@mui/material";

const items = ["BTC +2.4%", "ETH +1.8%", "EUR/USD -0.2%", "GOLD +0.6%"];

export default function MarketTicker() {
  return (
    <Box sx={{ display: "flex", gap: 2, overflow: "auto", py: 1 }}>
      {items.map((item) => (
        <Typography key={item} variant="caption" color="primary" whiteSpace="nowrap">
          {item}
        </Typography>
      ))}
    </Box>
  );
}
