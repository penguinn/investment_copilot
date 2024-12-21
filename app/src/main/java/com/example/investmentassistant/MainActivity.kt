class MainActivity : AppCompatActivity() {
    private val viewModel: StockViewModel by viewModels()
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        setupViewPager()
        observeData()
    }
    
    private fun setupViewPager() {
        // 设置ViewPager用于切换不同市场的数据
    }
    
    private fun observeData() {
        viewModel.stockData.observe(this) { data ->
            // 更新UI
        }
    }
} 