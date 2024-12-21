class StockRepository {
    private val api = RetrofitClient.stockApi
    
    suspend fun getStockIndices(market: String): List<StockIndex> {
        return api.getStockIndices(market)
    }
    
    suspend fun getKLineData(code: String, period: String): List<KLineData> {
        return api.getKLineData(code, period)
    }
} 