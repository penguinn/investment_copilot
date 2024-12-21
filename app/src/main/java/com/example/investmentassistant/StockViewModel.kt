class StockViewModel : ViewModel() {
    private val repository = StockRepository()
    private val _stockData = MutableLiveData<List<StockIndex>>()
    val stockData: LiveData<List<StockIndex>> = _stockData
    
    fun fetchStockData(market: String) {
        viewModelScope.launch {
            val result = repository.getStockIndices(market)
            _stockData.value = result
        }
    }
} 