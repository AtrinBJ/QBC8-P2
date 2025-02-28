// کد دیباگ برای بررسی مشکلات نمودار
document.addEventListener('DOMContentLoaded', function() {
    console.log("Analytics scripts loaded");

    // بررسی لود شدن Chart.js
    if (typeof Chart === 'undefined') {
        console.error("Chart.js library is not loaded!");
        // اضافه کردن پیام خطا به صفحه
        const errorMsg = document.createElement('div');
        errorMsg.className = 'alert alert-danger';
        errorMsg.textContent = 'خطا: کتابخانه Chart.js بارگذاری نشده است.';
        document.querySelector('.analytics-container').prepend(errorMsg);
    } else {
        console.log("Chart.js library is loaded successfully.");

        // چاپ نسخه Chart.js
        console.log("Chart.js version:", Chart.version);

        // تنظیم فونت پیش‌فرض برای تمام نمودارها
        Chart.defaults.font.family = 'Vazir, sans-serif';
        Chart.defaults.font.size = 14;
    }

    // بررسی داده‌های chartData
    if (typeof chartData === 'undefined') {
        console.error("chartData is not defined!");
    } else {
        console.log("chartData is available:", chartData);
    }

    // بررسی وجود عناصر canvas
    const canvases = document.querySelectorAll('canvas');
    console.log("Number of canvas elements:", canvases.length);
    canvases.forEach((canvas, index) => {
        console.log(`Canvas ${index} id:`, canvas.id);
    });

    // رنگ‌های سفارشی برای نمودارها - رنگ‌های مدرن‌تر
    const colors = {
        blue: 'rgba(80, 150, 250, 0.7)',
        blueLight: 'rgba(80, 150, 250, 0.1)',
        green: 'rgba(80, 250, 123, 0.7)',
        greenLight: 'rgba(80, 250, 123, 0.1)',
        red: 'rgba(255, 85, 85, 0.7)',
        redLight: 'rgba(255, 85, 85, 0.1)',
        orange: 'rgba(255, 184, 108, 0.7)',
        orangeLight: 'rgba(255, 184, 108, 0.1)',
        purple: 'rgba(189, 147, 249, 0.7)',
        purpleLight: 'rgba(189, 147, 249, 0.1)',
        yellow: 'rgba(241, 250, 140, 0.7)',
        yellowLight: 'rgba(241, 250, 140, 0.1)',
        pink: 'rgba(255, 121, 198, 0.7)',
        pinkLight: 'rgba(255, 121, 198, 0.1)',
        cyan: 'rgba(139, 233, 253, 0.7)',
        cyanLight: 'rgba(139, 233, 253, 0.1)',
    };

    // تعریف متغیرهای نمودار سراسری
    let timePerformanceChart = null;
    let timeChart = null;
    let categoryChart = null;
    let userPerformanceChart = null;
    let difficultyChart = null;
    let categoryRadarChart = null;
    let responseTimeChart = null;
    let questionsSuccessRateChart = null;
    let questionDifficultyDistributionChart = null;

    // حالت‌های فیلتر
    let activeFilters = {
        timeRange: 'all',
        difficulty: 'all',
        category: 'all',
        userSearch: '',
        userId: null,
        timeScale: 'day'  // مقیاس زمانی پیش‌فرض
    };

    // اضافه کردن رویداد دکمه نمایش نمودار راداری
    const displayRadarChartBtn = document.getElementById('displayRadarChart');
    if (displayRadarChartBtn) {
        displayRadarChartBtn.addEventListener('click', function() {
            const selectElement = document.getElementById('radarUserFilter');
            if (selectElement) {
                const username = selectElement.value;
                updateCategoryRadarChart(username);
            }
        });
    }

    // اضافه کردن رویداد دکمه نمایش نمودار زمان پاسخگویی
    const displayTimeResponseChartBtn = document.getElementById('displayTimeResponseChart');
    if (displayTimeResponseChartBtn) {
        displayTimeResponseChartBtn.addEventListener('click', function() {
            const selectElement = document.getElementById('timeResponseUserFilter');
            if (selectElement) {
                const username = selectElement.value;
                updateResponseTimeChart(username);
            }
        });
    }

    // اضافه کردن رویداد دکمه نمایش توزیع سختی سوالات
    const displayDifficultyDistributionBtn = document.getElementById('displayDifficultyDistribution');
    if (displayDifficultyDistributionBtn) {
        displayDifficultyDistributionBtn.addEventListener('click', function() {
            const selectElement = document.getElementById('difficultyDistributionCategory');
            if (selectElement) {
                const category = selectElement.value;
                fetchAndDisplayQuestionDifficultyDistribution(category);
            }
        });
    }

    // راه‌اندازی جستجوی کاربر
    setupUserSearch();

    // راه‌اندازی لیست نتایج جستجوی کاربر
    function setupUserSearch() {
        const searchInput = document.getElementById('userSearchInput');
        const searchResults = document.getElementById('userSearchResults');

        if (!searchInput || !searchResults) return;

        // پر کردن لیست اولیه کاربران
        //updateUserSearchResults('');

        // افزودن رویداد برای جستجو
        searchInput.addEventListener('input', function() {
            const query = this.value.trim().toLowerCase();
            updateUserSearchResults(query);
        });

        // افزودن رویداد برای نمایش لیست هنگام فوکوس
        searchInput.addEventListener('focus', function() {
            searchResults.style.display = 'block';
        });

        // مخفی کردن لیست وقتی کلیک خارج از لیست انجام می‌شود
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.style.display = 'none';
            }
        });
    }

    // به‌روزرسانی لیست نتایج جستجو
    function updateUserSearchResults(query) {
        const searchResults = document.getElementById('userSearchResults');

        if (!searchResults) return;

        // پاکسازی لیست فعلی
        searchResults.innerHTML = '';

        // جمع‌آوری کاربران از جدول‌ها
        const usersSet = new Set();
        const users = [];

        document.querySelectorAll('.user-row').forEach(row => {
            const userBtn = row.querySelector('.view-user-stats');
            if (userBtn) {
                const userId = userBtn.getAttribute('data-user-id');
                const username = row.getAttribute('data-username');

                // اضافه کردن فقط کاربران غیر تکراری
                if (username && !usersSet.has(username)) {
                    usersSet.add(username);
                    users.push({ id: userId, username: username });
                }
            }
        });

        // فیلتر کردن کاربران بر اساس کوئری
        const filteredUsers = users.filter(user =>
            user.username.toLowerCase().includes(query.toLowerCase())
        );

        // اگر نتیجه‌ای وجود نداشت
        if (filteredUsers.length === 0) {
            searchResults.innerHTML = '<div class="user-search-item">هیچ کاربری یافت نشد</div>';
            searchResults.style.display = 'block';
            return;
        }

        // افزودن کاربران فیلتر شده به لیست
        filteredUsers.forEach(user => {
            const item = document.createElement('div');
            item.className = 'user-search-item';
            item.textContent = user.username;
            item.setAttribute('data-user-id', user.id);

            // رویداد کلیک برای انتخاب کاربر
            item.addEventListener('click', function() {
                // تنظیم مقدار در فیلد جستجو
                document.getElementById('userSearchInput').value = user.username;

                // اعمال فیلتر کاربر
                activeFilters.userId = user.id;
                activeFilters.userSearch = user.username;

                // به‌روزرسانی فیلترها
                applyFilters();

                // مخفی کردن لیست
                searchResults.style.display = 'none';
            });

            searchResults.appendChild(item);
        });

        // نمایش لیست
        searchResults.style.display = 'block';
    }

    // اعمال فیلترها
    function applyFilters() {
        console.log("Applying filters:", activeFilters);

        // نمایش فیلترهای فعال
        updateActiveFilterDisplay();

        // فیلتر کردن ردیف‌های کاربران
        filterUserRows();

        // فیلتر کردن ردیف‌های دسته‌بندی‌ها
        filterCategoryRows();

        // به‌روزرسانی نمودارها
        fetchFilteredData();
    }

    // نمایش فیلترهای فعال
    function updateActiveFilterDisplay() {
        const activeFilterBadges = document.getElementById('activeFilterBadges');
        const activeFiltersContainer = document.getElementById('activeFilters');

        if (!activeFilterBadges || !activeFiltersContainer) return;

        let hasActiveFilters = false;
        let badgeHTML = '';

        if (activeFilters.timeRange !== 'all') {
            hasActiveFilters = true;
            let timeText = '';
            switch(activeFilters.timeRange) {
                case '1m': timeText = '۱ ماه اخیر'; break;
                case '3m': timeText = '۳ ماه اخیر'; break;
                case '1y': timeText = '۱ سال اخیر'; break;
            }
            badgeHTML += `<span class="badge bg-info me-1 mb-1">بازه زمانی: ${timeText}</span>`;
        }

        if (activeFilters.difficulty !== 'all') {
            hasActiveFilters = true;
            let difficultyText = '';
            switch(activeFilters.difficulty) {
                case 'easy': difficultyText = 'آسان'; break;
                case 'medium': difficultyText = 'متوسط'; break;
                case 'hard': difficultyText = 'سخت'; break;
            }
            badgeHTML += `<span class="badge bg-info me-1 mb-1">سطح دشواری: ${difficultyText}</span>`;
        }

        if (activeFilters.category !== 'all') {
            hasActiveFilters = true;
            badgeHTML += `<span class="badge bg-info me-1 mb-1">دسته‌بندی: ${activeFilters.category}</span>`;
        }

        if (activeFilters.userSearch) {
            hasActiveFilters = true;
            badgeHTML += `<span class="badge bg-info me-1 mb-1">کاربر: ${activeFilters.userSearch}</span>`;
        }

        if (activeFilters.timeScale !== 'day') {
            hasActiveFilters = true;
            let timeScaleText = '';
            switch(activeFilters.timeScale) {
                case 'month': timeScaleText = 'ماهانه'; break;
                case 'year': timeScaleText = 'سالانه'; break;
            }
            badgeHTML += `<span class="badge bg-info me-1 mb-1">مقیاس زمانی: ${timeScaleText}</span>`;
        }

        activeFilterBadges.innerHTML = badgeHTML;

        if (hasActiveFilters) {
            activeFiltersContainer.classList.remove('d-none');
        } else {
            activeFiltersContainer.classList.add('d-none');
        }
    }

    // فیلتر کردن ردیف‌های کاربران
    function filterUserRows() {
        const userRows = document.querySelectorAll('.user-row');

        userRows.forEach(row => {
            const username = row.getAttribute('data-username').toLowerCase();
            let showRow = true;

            // فیلتر جستجوی کاربر
            if (activeFilters.userSearch && !username.includes(activeFilters.userSearch.toLowerCase())) {
                showRow = false;
            }

            // نمایش یا مخفی کردن ردیف
            row.style.display = showRow ? '' : 'none';
        });
    }

    // فیلتر کردن ردیف‌های دسته‌بندی‌ها
    function filterCategoryRows() {
        const categoryRows = document.querySelectorAll('.category-row');

        categoryRows.forEach(row => {
            const category = row.getAttribute('data-category');
            let showRow = true;

            // فیلتر دسته‌بندی
            if (activeFilters.category !== 'all' && category !== activeFilters.category) {
                showRow = false;
            }

            // نمایش یا مخفی کردن ردیف
            row.style.display = showRow ? '' : 'none';
        });
    }

    // دریافت داده‌های فیلتر شده از سرور
    async function fetchFilteredData() {
        try {
            // ارسال درخواست به سرور
            const response = await fetch('/admin/analytics/filter', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify(activeFilters)
            });

            if (!response.ok) {
                throw new Error(`خطای سرور: ${response.status}`);
            }

            const data = await response.json();
            console.log("Filtered data received:", data);

            // به‌روزرسانی نمودارها با داده‌های جدید
            updateCharts(data);

        } catch (error) {
            console.error("Error fetching filtered data:", error);
            // نمایش پیام خطا
            alert(`خطا در دریافت داده‌های فیلتر شده: ${error.message}`);
        }
    }

    // به‌روزرسانی همه نمودارها با داده‌های جدید
    function updateCharts(data) {
        updateTimePerformanceChart(data);
        updateTimeChart(data);
        updateCategoryChart(data);
        updateUserPerformanceChart(data);
        updateDifficultyChart(data);
    }

    // راه‌اندازی رویدادهای فیلتر
    function setupFilterEventListeners() {
        // رویداد فیلتر بازه زمانی (لیست کشویی)
        const timeRangeFilter = document.getElementById('timeRangeFilter');
        if (timeRangeFilter) {
            timeRangeFilter.addEventListener('change', function() {
                activeFilters.timeRange = this.value;
                applyFilters();
            });
        }

        // رویداد فیلتر سطح دشواری (لیست کشویی)
        const difficultyFilter = document.getElementById('difficultyFilter');
        if (difficultyFilter) {
            difficultyFilter.addEventListener('change', function() {
                activeFilters.difficulty = this.value;
                applyFilters();
            });
        }

        // رویداد فیلتر دسته‌بندی (لیست کشویی)
        const categoryFilter = document.getElementById('categoryFilter');
        if (categoryFilter) {
            categoryFilter.addEventListener('change', function() {
                activeFilters.category = this.value;
                applyFilters();
            });
        }

        // رویداد فیلتر مقیاس زمانی
        document.querySelectorAll('.time-scale-btn').forEach(button => {
            button.addEventListener('click', function() {
                document.querySelectorAll('.time-scale-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                this.classList.add('active');
                activeFilters.timeScale = this.getAttribute('data-time-scale');
                updateTimePerformanceChart();
            });
        });

        // رویداد پاک کردن همه فیلترها
        const clearAllFiltersBtn = document.getElementById('clearAllFilters');
        if (clearAllFiltersBtn) {
            clearAllFiltersBtn.addEventListener('click', function() {
                // پاک کردن تمام فیلترها
                activeFilters = {
                    timeRange: 'all',
                    difficulty: 'all',
                    category: 'all',
                    userSearch: '',
                    userId: null,
                    timeScale: 'day'
                };

                // بازنشانی وضعیت فیلترها - لیست‌های کشویی
                document.getElementById('timeRangeFilter').value = 'all';
                document.getElementById('difficultyFilter').value = 'all';
                document.getElementById('categoryFilter').value = 'all';

                // بازنشانی وضعیت فیلتر مقیاس زمانی
                document.querySelectorAll('.time-scale-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                document.querySelector('.time-scale-btn[data-time-scale="day"]').classList.add('active');

                // پاک کردن جستجوی کاربر
                document.getElementById('userSearchInput').value = '';

                // اعمال فیلترها
                applyFilters();
            });
        }

        // رویداد دکمه‌های مشاهده آمار کاربر
        document.querySelectorAll('.view-user-stats').forEach(button => {
            button.addEventListener('click', function() {
                const userId = this.getAttribute('data-user-id');
                const username = this.getAttribute('data-username');

                // تنظیم فیلتر کاربر
                activeFilters.userId = userId;
                activeFilters.userSearch = username;

                // تنظیم مقدار در فیلد جستجو
                document.getElementById('userSearchInput').value = username;

                // اعمال فیلترها
                applyFilters();

                // اسکرول به بالای صفحه
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        });
    }

    // راه‌اندازی دکمه دانلود گزارش
    function setupDownloadButton() {
        const downloadBtn = document.getElementById('downloadReport');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', async function() {
                try {
                    // نمایش وضعیت بارگذاری
                    downloadBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i> در حال آماده‌سازی...';
                    downloadBtn.disabled = true;

                    // درخواست دانلود گزارش
                    const response = await fetch('/admin/analytics/download', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        body: JSON.stringify(activeFilters)
                    });

                    if (!response.ok) {
                        throw new Error(`خطای سرور: ${response.status}`);
                    }

                    // تبدیل پاسخ به blob
                    const blob = await response.blob();

                    // ایجاد لینک دانلود
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = url;

                    // نام فایل
                    const filename = response.headers.get('content-disposition')?.split('filename=')[1]?.replace(/"/g, '') || 'quiz_analytics_report.xlsx';
                    a.download = filename;

                    // اضافه به document و کلیک
                    document.body.appendChild(a);
                    a.click();

                    // پاکسازی
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);

                } catch (error) {
                    console.error("Error downloading report:", error);
                    alert(`خطا در دانلود گزارش: ${error.message}`);
                } finally {
                    // بازگرداندن دکمه به حالت اولیه
                    downloadBtn.innerHTML = '<i class="bi bi-file-earmark-excel me-1"></i> دانلود گزارش Excel';
                    downloadBtn.disabled = false;
                }
            });
        }
    }

    // ---------- ایجاد نمودارها ----------

    // نمودار روند زمانی عملکرد - رفع مشکل اندازه
    function initTimePerformanceChart() {
        const ctx = document.getElementById('timePerformanceChart');
        if (!ctx) return;

        // بررسی وجود داده
        if (!chartData || !chartData.time_labels || chartData.time_labels.length === 0) {
            console.warn("No time performance data available");
            return;
        }

        // اصلاح: تنظیم اندازه نمودار
        timePerformanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.time_labels,
                datasets: [{
                    label: 'میانگین نمرات',
                    data: chartData.time_scores,
                    borderColor: colors.blue,
                    backgroundColor: colors.blueLight,
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: colors.blue,
                    pointBorderColor: '#fff',
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                aspectRatio: 2,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 14
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(40, 42, 54, 0.8)',
                        titleColor: '#8be9fd',
                        bodyColor: '#f8f8f2',
                        borderColor: '#6272a4',
                        borderWidth: 1,
                        bodyFont: {
                            family: 'Vazir, sans-serif'
                        },
                        titleFont: {
                            family: 'Vazir, sans-serif'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(98, 114, 164, 0.2)'
                        },
                        ticks: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 12
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(98, 114, 164, 0.2)'
                        },
                        ticks: {
                            color: '#f8f8f2',
                            maxRotation: 45,
                            minRotation: 45,
                            autoSkip: true,
                            maxTicksLimit: 10,
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 12
                            }
                        }
                    }
                }
            }
        });
    }

    // به‌روزرسانی نمودار روند زمانی - اصلاح شده بدون دکمه‌های نمرات، تعداد و زمان
    function updateTimePerformanceChart(data) {
        if (!timePerformanceChart) return;

        // استفاده از داده‌های فیلتر شده یا داده‌های موجود
        let timeLabels = data ? data.time_labels : chartData.time_labels;

        // همیشه از نمرات استفاده می‌کنیم (بدون امکان فیلتر)
        let chartDataValues = data ? data.time_scores : chartData.time_scores;
        let chartLabel = 'میانگین نمرات';
        let chartColor = colors.blue;
        let chartBgColor = colors.blueLight;

        // اعمال مقیاس زمانی روی داده‌ها
        const formattedData = formatDataByTimeScale(timeLabels, chartDataValues, activeFilters.timeScale);

        timePerformanceChart.data.labels = formattedData.labels;
        timePerformanceChart.data.datasets[0].label = chartLabel;
        timePerformanceChart.data.datasets[0].data = formattedData.values;
        timePerformanceChart.data.datasets[0].borderColor = chartColor;
        timePerformanceChart.data.datasets[0].backgroundColor = chartBgColor;
        timePerformanceChart.data.datasets[0].pointBackgroundColor = chartColor;

        // بهبود تنظیمات فونت
        timePerformanceChart.options.plugins.legend.labels.font = {
            family: 'Vazir, sans-serif',
            size: 14
        };

        timePerformanceChart.options.scales.x.ticks.font = {
            family: 'Vazir, sans-serif',
            size: 12
        };

        timePerformanceChart.options.scales.y.ticks.font = {
            family: 'Vazir, sans-serif',
            size: 12
        };

        timePerformanceChart.update();
    }

    // تابع تبدیل داده‌ها بر اساس مقیاس زمانی
    function formatDataByTimeScale(labels, values, timeScale) {
        if (!labels || !values || labels.length === 0 || values.length === 0) {
            return { labels: [], values: [] };
        }

        // تبدیل تاریخ‌ها به شی تاریخ
        const dateValues = labels.map(label => {
            // فرض می‌کنیم قالب تاریخ 'YYYY-MM-DD' است
            return new Date(label);
        });

        // اگر مقیاس روز باشد، همان داده‌ها را برگردان
        if (timeScale === 'day') {
            // فقط قالب نمایش تاریخ را تغییر می‌دهیم
            const formattedLabels = dateValues.map(date => {
                return new Intl.DateTimeFormat('fa-IR', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                }).format(date);
            });

            return {
                labels: formattedLabels,
                values: values
            };
        }

        // گروه‌بندی بر اساس ماه یا سال
        const groupedData = {};

        dateValues.forEach((date, index) => {
            let key;

            if (timeScale === 'month') {
                // کلید: 'YYYY-MM'
                key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
            } else if (timeScale === 'year') {
                // کلید: 'YYYY'
                key = String(date.getFullYear());
            }

            if (!groupedData[key]) {
                groupedData[key] = {
                    sum: 0,
                    count: 0
                };
            }

            groupedData[key].sum += values[index];
            groupedData[key].count++;
        });

        // محاسبه میانگین برای هر گروه
        const groupKeys = Object.keys(groupedData).sort();
        const groupedLabels = [];
        const groupedValues = [];

        groupKeys.forEach(key => {
            let displayLabel;

            if (timeScale === 'month') {
                // جدا کردن سال و ماه
                const [year, month] = key.split('-');
                // نمایش به فرمت فارسی
                displayLabel = new Intl.DateTimeFormat('fa-IR', {
                    year: 'numeric',
                    month: 'long'
                }).format(new Date(year, parseInt(month) - 1, 1));
            } else if (timeScale === 'year') {
                // نمایش به فرمت فارسی
                displayLabel = new Intl.DateTimeFormat('fa-IR', {
                    year: 'numeric'
                }).format(new Date(key, 0, 1));
            }

            groupedLabels.push(displayLabel);
            // میانگین مقادیر برای این گروه
            groupedValues.push(groupedData[key].sum / groupedData[key].count);
        });

        return {
            labels: groupedLabels,
            values: groupedValues
        };
    }

    // نمودار روند زمانی
    function initTimeChart() {
        const ctx = document.getElementById('timeChart');
        if (!ctx) return;

        // بررسی وجود داده
        if (!chartData || !chartData.time_labels || chartData.time_labels.length === 0) {
            console.warn("No time chart data available");
            return;
        }

        // اصلاح: تنظیم اندازه نمودار
        timeChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.time_labels,
                datasets: [
                    {
                        label: 'تعداد کوییزها',
                        data: chartData.time_counts,
                        borderColor: colors.blue,
                        backgroundColor: colors.blueLight,
                        borderWidth: 2,
                        tension: 0.4,
                        yAxisID: 'y',
                        fill: true
                    },
                    {
                        label: 'میانگین نمرات',
                        data: chartData.time_scores,
                        borderColor: colors.green,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        tension: 0.4,
                        yAxisID: 'y1',
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                aspectRatio: 2,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 14
                            }
                        }
                    },
                    tooltip: {
                        bodyFont: {
                            family: 'Vazir, sans-serif'
                        },
                        titleFont: {
                            family: 'Vazir, sans-serif'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'تعداد کوییزها',
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif'
                            }
                        },
                        ticks: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 12
                            }
                        },
                        grid: {
                            color: 'rgba(98, 114, 164, 0.2)'
                        }
                    },
                    y1: {
                        beginAtZero: true,
                        max: 100,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'میانگین نمرات (%)',
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif'
                            }
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                        ticks: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 12
                            }
                        }
                    },
                    x: {
                        ticks: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 12
                            },
                            maxRotation: 45,
                            minRotation: 45,
                            autoSkip: true,
                            maxTicksLimit: 8
                        },
                        grid: {
                            color: 'rgba(98, 114, 164, 0.2)'
                        }
                    }
                }
            }
        });
    }

    // به‌روزرسانی نمودار روند زمانی
    function updateTimeChart(data) {
        if (!timeChart) return;

        const timeLabels = data ? data.time_labels : chartData.time_labels;
        const timeCounts = data ? data.time_counts : chartData.time_counts;
        const timeScores = data ? data.time_scores : chartData.time_scores;

        timeChart.data.labels = timeLabels;
        timeChart.data.datasets[0].data = timeCounts;
        timeChart.data.datasets[1].data = timeScores;

        timeChart.update();
    }

    // نمودار عملکرد دسته‌بندی‌ها
    function initCategoryChart() {
        const ctx = document.getElementById('categoryChart');
        if (!ctx) return;

        // بررسی وجود داده
        if (!chartData || !chartData.categories || chartData.categories.length === 0) {
            console.warn("No category chart data available");
            return;
        }

        categoryChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartData.categories,
                datasets: [
                    {
                        label: 'تعداد شرکت‌کنندگان',
                        data: chartData.category_counts,
                        backgroundColor: colors.blue,
                        borderColor: colors.blue,
                        borderWidth: 1,
                        borderRadius: 4,
                        yAxisID: 'y',
                    },
                    {
                        label: 'میانگین نمرات',
                        data: chartData.category_scores,
                        backgroundColor: colors.green,
                        borderColor: colors.green,
                        borderWidth: 2,
                        type: 'line',
                        yAxisID: 'y1',
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                aspectRatio: 2,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 14
                            }
                        }
                    },
                    tooltip: {
                        bodyFont: {
                            family: 'Vazir, sans-serif'
                        },
                        titleFont: {
                            family: 'Vazir, sans-serif'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'تعداد شرکت‌کنندگان',
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif'
                            }
                        },
                        ticks: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 12
                            }
                        },
                        grid: {
                            color: 'rgba(98, 114, 164, 0.2)'
                        }
                    },
                    y1: {
                        beginAtZero: true,
                        max: 100,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'میانگین نمرات (%)',
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif'
                            }
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                        ticks: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 12
                            }
                        }
                    },
                    x: {
                        ticks: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 12
                            }
                        },
                        grid: {
                            color: 'rgba(98, 114, 164, 0.2)'
                        }
                    }
                }
            }
        });
    }

    // به‌روزرسانی نمودار دسته‌بندی‌ها
    function updateCategoryChart(data) {
        if (!categoryChart) return;

        const categories = data ? data.categories : chartData.categories;
        const categoryCounts = data ? data.category_counts : chartData.category_counts;
        const categoryScores = data ? data.category_scores : chartData.category_scores;

        categoryChart.data.labels = categories;
        categoryChart.data.datasets[0].data = categoryCounts;
        categoryChart.data.datasets[1].data = categoryScores;

        categoryChart.update();
    }

    // نمودار عملکرد کاربران
    function initUserPerformanceChart() {
        const ctx = document.getElementById('userPerformanceChart');
        if (!ctx) return;

        // بررسی وجود داده
        if (!chartData || !chartData.users || chartData.users.length === 0) {
            console.warn("No user performance data available");
            return;
        }

        userPerformanceChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: chartData.users,
                datasets: [
                    {
                        label: 'تعداد کوییزها',
                        data: chartData.user_counts,
                        backgroundColor: colors.orange,
                        borderColor: colors.orange,
                        borderWidth: 1,
                        borderRadius: 4,
                        yAxisID: 'y',
                    },
                    {
                        label: 'میانگین نمرات',
                        data: chartData.user_scores,
                        backgroundColor: colors.cyan,
                        borderColor: colors.cyan,
                        borderWidth: 2,
                        type: 'line',
                        fill: false,
                        yAxisID: 'y1',
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                aspectRatio: 2,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 14
                            }
                        }
                    },
                    tooltip: {
                        bodyFont: {
                            family: 'Vazir, sans-serif'
                        },
                        titleFont: {
                            family: 'Vazir, sans-serif'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'تعداد کوییزها',
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif'
                            }
                        },
                        ticks: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 12
                            }
                        },
                        grid: {
                            color: 'rgba(98, 114, 164, 0.2)'
                        }
                    },
                    y1: {
                        beginAtZero: true,
                        max: 100,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'میانگین نمرات (%)',
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif'
                            }
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                        ticks: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 12
                            }
                        }
                    },
                    x: {
                        ticks: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 12
                            }
                        },
                        grid: {
                            color: 'rgba(98, 114, 164, 0.2)'
                        }
                    }
                }
            }
        });
    }

    // به‌روزرسانی نمودار عملکرد کاربران
    function updateUserPerformanceChart(data) {
        if (!userPerformanceChart) return;

        // اگر داده‌های کاربران در داده‌های فیلتر شده وجود نداشت
        if (data && (!data.users || data.users.length === 0)) {
            userPerformanceChart.data.labels = chartData.users;
            userPerformanceChart.data.datasets[0].data = chartData.user_counts;
            userPerformanceChart.data.datasets[1].data = chartData.user_scores;
        } else if (data) {
            userPerformanceChart.data.labels = data.users;
            userPerformanceChart.data.datasets[0].data = data.user_counts;
            userPerformanceChart.data.datasets[1].data = data.user_scores;
        }

        userPerformanceChart.update();
    }

    // نمودار سطوح دشواری
    function initDifficultyChart() {
        const ctx = document.getElementById('difficultyChart');
        if (!ctx) return;

        // بررسی وجود داده
        if (!chartData || !chartData.difficulty_labels || chartData.difficulty_labels.length === 0) {
            console.warn("No difficulty chart data available");
            return;
        }

        difficultyChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: chartData.difficulty_labels,
                datasets: [{
                    data: chartData.difficulty_counts,
                    backgroundColor: [colors.green, colors.yellow, colors.red],
                    borderColor: 'rgba(40, 42, 54, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                aspectRatio: 2,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 14
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(40, 42, 54, 0.8)',
                        titleColor: '#8be9fd',
                        bodyColor: '#f8f8f2',
                        bodyFont: {
                            family: 'Vazir, sans-serif'
                        },
                        titleFont: {
                            family: 'Vazir, sans-serif'
                        }
                    }
                }
            }
        });
    }

    // تابع بهبود یافته برای نمایش جزئیات سطح دشواری
    function enhanceDifficultyChart() {
        const difficultyChartElement = document.getElementById('difficultyChart');
        if (!difficultyChartElement) return;

        // بررسی وجود داده‌های تفصیلی سطح دشواری
        if (!chartData || !chartData.difficulty_detailed) {
            console.warn("No detailed difficulty data available");
            return;
        }

        // اضافه کردن توضیحات جزئی‌تر به tooltip
        if (difficultyChart) {
            difficultyChart.options.plugins.tooltip.callbacks = {
                label: function(context) {
                    const label = context.label || '';
                    const value = context.raw || 0;
                    const diffData = chartData.difficulty_detailed[label];

                    if (!diffData) return `${label}: ${value} کوییز`;

                    return [
                        `${label}: ${value} کوییز`,
                        `میانگین نمره: ${diffData.avg_score.toFixed(1)}%`,
                        `میانگین زمان: ${diffData.avg_time.toFixed(1)} ثانیه`
                    ];
                }
            };

            difficultyChart.update();
        }

        // ساخت دستی HTML برای جزئیات سطوح دشواری
        const detailsHTML = `
        <div class="row mt-4">
            <div class="col-md-4">
                <div class="card bg-danger bg-opacity-25 h-100">
                    <div class="card-body text-center">
                        <h5 class="card-title text-danger">سطح سخت</h5>
                        <div class="mt-3">
                            <p class="mb-2">تعداد کوییزها: <strong>${chartData.difficulty_detailed['سخت'].count}</strong></p>
                            <p class="mb-2">میانگین نمره: <strong>${chartData.difficulty_detailed['سخت'].avg_score.toFixed(1)}%</strong></p>
                            <p class="mb-2">میانگین زمان: <strong>${chartData.difficulty_detailed['سخت'].avg_time.toFixed(1)} ثانیه</strong></p>
                            <p class="mb-0">دسته‌بندی‌های متداول:</p>
                            <div class="mt-2">
                                ${getDifficultyCategoriesHTML('سخت')}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-md-4">
                <div class="card bg-warning bg-opacity-25 h-100">
                    <div class="card-body text-center">
                        <h5 class="card-title text-warning">سطح متوسط</h5>
                        <div class="mt-3">
                            <p class="mb-2">تعداد کوییزها: <strong>${chartData.difficulty_detailed['متوسط'].count}</strong></p>
                            <p class="mb-2">میانگین نمره: <strong>${chartData.difficulty_detailed['متوسط'].avg_score.toFixed(1)}%</strong></p>
                            <p class="mb-2">میانگین زمان: <strong>${chartData.difficulty_detailed['متوسط'].avg_time.toFixed(1)} ثانیه</strong></p>
                            <p class="mb-0">دسته‌بندی‌های متداول:</p>
                            <div class="mt-2">
                                ${getDifficultyCategoriesHTML('متوسط')}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-md-4">
                <div class="card bg-success bg-opacity-25 h-100">
                    <div class="card-body text-center">
                        <h5 class="card-title text-success">سطح آسان</h5>
                        <div class="mt-3">
                            <p class="mb-2">تعداد کوییزها: <strong>${chartData.difficulty_detailed['آسان'].count}</strong></p>
                            <p class="mb-2">میانگین نمره: <strong>${chartData.difficulty_detailed['آسان'].avg_score.toFixed(1)}%</strong></p>
                            <p class="mb-2">میانگین زمان: <strong>${chartData.difficulty_detailed['آسان'].avg_time.toFixed(1)} ثانیه</strong></p>
                            <p class="mb-0">دسته‌بندی‌های متداول:</p>
                            <div class="mt-2">
                                ${getDifficultyCategoriesHTML('آسان')}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `;

        // پاک کردن جزئیات قبلی اگر وجود داشته باشد
        const existingDetails = difficultyChartElement.parentNode.querySelector('.difficulty-details');
        if (existingDetails) {
            existingDetails.remove();
        }

        // اضافه کردن جزئیات جدید
        const detailsElement = document.createElement('div');
        detailsElement.className = 'difficulty-details col-md-6';
        detailsElement.innerHTML = detailsHTML;
        difficultyChartElement.parentNode.appendChild(detailsElement);

        console.log("Difficulty details added successfully");
    }

    // تابع کمکی برای ساخت HTML دسته‌بندی‌های متداول در هر سطح دشواری
    function getDifficultyCategoriesHTML(difficultyLevel) {
        if (!chartData.difficulty_detailed[difficultyLevel] ||
            !chartData.difficulty_detailed[difficultyLevel].categories) {
            return '<span class="badge bg-secondary">داده‌ای موجود نیست</span>';
        }

        const categories = chartData.difficulty_detailed[difficultyLevel].categories;
        const sortedCategories = Object.entries(categories)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 3); // نمایش حداکثر 3 دسته‌بندی پرتکرار

        if (sortedCategories.length === 0) {
            return '<span class="badge bg-secondary">داده‌ای موجود نیست</span>';
        }

        return sortedCategories.map(([category, count]) =>
            `<span class="badge bg-secondary me-1">${category} (${count})</span>`
        ).join(' ');
    }

    // به‌روزرسانی نمودار سطوح دشواری
    function updateDifficultyChart(data) {
        if (!difficultyChart) return;

        // اگر داده‌های سطح دشواری در داده‌های فیلتر شده وجود داشت
        if (data && data.difficulty_labels && data.difficulty_counts) {
            difficultyChart.data.labels = data.difficulty_labels;
            difficultyChart.data.datasets[0].data = data.difficulty_counts;
        }

        difficultyChart.update();
    }

    // نمودار راداری برای نمایش قوت و ضعف کاربران در دسته‌بندی‌ها
    function initCategoryRadarChart() {
        const ctx = document.getElementById('categoryRadarChart');
        if (!ctx) {
            console.warn("Category radar chart element not found");
            return;
        }

        // بررسی وجود داده
        if (!chartData || !chartData.category_strength || Object.keys(chartData.category_strength).length === 0) {
            console.warn("No category strength data available");
            return;
        }

        // اولین کاربر را به عنوان پیش‌فرض انتخاب می‌کنیم
        const firstUser = Object.keys(chartData.category_strength)[0];
        const userData = chartData.category_strength[firstUser];

        // ساخت نمودار راداری
        categoryRadarChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: userData.categories,
                datasets: [{
                    label: firstUser,
                    data: userData.scores,
                    backgroundColor: colors.purpleLight,
                    borderColor: colors.purple,
                    borderWidth: 2,
                    pointBackgroundColor: colors.purple,
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: colors.purple,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                aspectRatio: 1.5,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 14
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(40, 42, 54, 0.8)',
                        titleColor: '#8be9fd',
                        bodyColor: '#f8f8f2',
                        bodyFont: {
                            family: 'Vazir, sans-serif'
                        },
                        titleFont: {
                            family: 'Vazir, sans-serif'
                        }
                    }
                },
                scales: {
                    r: {
                        angleLines: {
                            color: 'rgba(98, 114, 164, 0.2)'
                        },
                        grid: {
                            color: 'rgba(98, 114, 164, 0.2)'
                        },
                        pointLabels: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 12
                            }
                        },
                        ticks: {
                            color: '#f8f8f2',
                            backdropColor: 'transparent',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 10
                            }
                        },
                        suggestedMin: 0,
                        suggestedMax: 100
                    }
                }
            }
        });
    }

    // تابع به‌روزرسانی نمودار راداری - اصلاح شده
    function updateCategoryRadarChart(username) {
        if (!categoryRadarChart) return;

        console.log("Updating radar chart for user:", username);

        if (username === 'all') {
            // نمایش میانگین همه کاربران در هر دسته‌بندی
            const allCategories = new Set();
            const categoryScores = {};
            const categoryCounts = {};

            // جمع‌آوری تمام دسته‌بندی‌ها و داده‌ها
            Object.values(chartData.category_strength).forEach(userData => {
                userData.categories.forEach((category, index) => {
                    allCategories.add(category);
                    if (!categoryScores[category]) {
                        categoryScores[category] = 0;
                        categoryCounts[category] = 0;
                    }
                    categoryScores[category] += userData.scores[index];
                    categoryCounts[category]++;
                });
            });

            // محاسبه میانگین هر دسته‌بندی
            const categories = Array.from(allCategories);
            const averageScores = categories.map(category =>
                categoryCounts[category] > 0 ? categoryScores[category] / categoryCounts[category] : 0
            );

            // به‌روزرسانی نمودار
            categoryRadarChart.data.labels = categories;
            categoryRadarChart.data.datasets[0].label = 'میانگین همه کاربران';
            categoryRadarChart.data.datasets[0].data = averageScores;
            categoryRadarChart.data.datasets[0].backgroundColor = colors.blueLight;
            categoryRadarChart.data.datasets[0].borderColor = colors.blue;
            categoryRadarChart.data.datasets[0].pointBackgroundColor = colors.blue;
            categoryRadarChart.data.datasets[0].pointHoverBorderColor = colors.blue;

        } else if (chartData.category_strength && chartData.category_strength[username]) {
            // نمایش داده‌های کاربر خاص
            const userData = chartData.category_strength[username];
            categoryRadarChart.data.labels = userData.categories;
            categoryRadarChart.data.datasets[0].label = username;
            categoryRadarChart.data.datasets[0].data = userData.scores;
            categoryRadarChart.data.datasets[0].backgroundColor = colors.purpleLight;
            categoryRadarChart.data.datasets[0].borderColor = colors.purple;
            categoryRadarChart.data.datasets[0].pointBackgroundColor = colors.purple;
            categoryRadarChart.data.datasets[0].pointHoverBorderColor = colors.purple;
        } else {
            console.warn(`No category strength data found for user: ${username}`);
            // نمایش پیام خطا به کاربر
            alert(`داده‌ای برای کاربر ${username} یافت نشد!`);
            return;
        }

        // اعمال انیمیشن به نمودار
        const chartElement = document.getElementById('categoryRadarChart');
        if (chartElement) {
            chartElement.classList.add('filter-change');
            setTimeout(() => {
                chartElement.classList.remove('filter-change');
            }, 500);
        }

        categoryRadarChart.update();
    }

    // نمودار زمان پاسخگویی
    function initResponseTimeChart() {
        const ctx = document.getElementById('responseTimeChart');
        if (!ctx) {
            console.warn("Response time chart element not found");
            return;
        }

        // بررسی وجود داده
        if (!chartData || !chartData.response_time || Object.keys(chartData.response_time).length === 0) {
            console.warn("No response time data available");
            return;
        }

        // اولین کاربر را به عنوان پیش‌فرض انتخاب می‌کنیم
        const firstUser = Object.keys(chartData.response_time)[0];
        const userData = chartData.response_time[firstUser];

        // ساخت نمودار زمان پاسخگویی
        responseTimeChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: userData.dates,
                datasets: [{
                    label: `زمان پاسخگویی ${firstUser}`,
                    data: userData.times,
                    borderColor: colors.cyan,
                    backgroundColor: colors.cyanLight,
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: colors.cyan,
                    pointBorderColor: '#fff',
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                aspectRatio: 2,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 14
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(40, 42, 54, 0.8)',
                        titleColor: '#8be9fd',
                        bodyColor: '#f8f8f2',
                        bodyFont: {
                            family: 'Vazir, sans-serif'
                        },
                        titleFont: {
                            family: 'Vazir, sans-serif'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'زمان (ثانیه)',
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif'
                            }
                        },
                        ticks: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 12
                            }
                        },
                        grid: {
                            color: 'rgba(98, 114, 164, 0.2)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 12
                            },
                            maxRotation: 45,
                            minRotation: 45
                        },
                        grid: {
                            color: 'rgba(98, 114, 164, 0.2)'
                        }
                    }
                }
            }
        });
    }

    // تابع به‌روزرسانی نمودار زمان پاسخگویی - اصلاح شده
    function updateResponseTimeChart(username) {
        if (!responseTimeChart) return;

        console.log("Updating response time chart for user:", username);

        if (username === 'all') {
            // ساخت میانگین زمان پاسخگویی روزانه برای همه کاربران
            const allDates = new Set();
            const dateTimes = {};
            const dateCounts = {};

            // جمع‌آوری تمام تاریخ‌ها و داده‌ها
            Object.values(chartData.response_time).forEach(userData => {
                userData.dates.forEach((date, index) => {
                    allDates.add(date);
                    if (!dateTimes[date]) {
                        dateTimes[date] = 0;
                        dateCounts[date] = 0;
                    }
                    dateTimes[date] += userData.times[index];
                    dateCounts[date]++;
                });
            });

            // محاسبه میانگین هر روز
            const dates = Array.from(allDates).sort();
            const averageTimes = dates.map(date =>
                dateCounts[date] > 0 ? dateTimes[date] / dateCounts[date] : 0
            );

            // به‌روزرسانی نمودار
            responseTimeChart.data.labels = dates;
            responseTimeChart.data.datasets[0].label = 'میانگین زمان پاسخگویی همه کاربران';
            responseTimeChart.data.datasets[0].data = averageTimes;
            responseTimeChart.data.datasets[0].borderColor = colors.green;
            responseTimeChart.data.datasets[0].backgroundColor = colors.greenLight;
            responseTimeChart.data.datasets[0].pointBackgroundColor = colors.green;

        } else if (chartData.response_time && chartData.response_time[username]) {
            // نمایش داده‌های کاربر خاص
            const userData = chartData.response_time[username];
            responseTimeChart.data.labels = userData.dates;
            responseTimeChart.data.datasets[0].label = `زمان پاسخگویی ${username}`;
            responseTimeChart.data.datasets[0].data = userData.times;
            responseTimeChart.data.datasets[0].borderColor = colors.cyan;
            responseTimeChart.data.datasets[0].backgroundColor = colors.cyanLight;
            responseTimeChart.data.datasets[0].pointBackgroundColor = colors.cyan;
        } else {
            console.warn(`No response time data found for user: ${username}`);
            // نمایش پیام خطا به کاربر
            alert(`داده‌ای برای کاربر ${username} یافت نشد!`);
            return;
        }

        // اعمال انیمیشن به نمودار
        const chartElement = document.getElementById('responseTimeChart');
        if (chartElement) {
            chartElement.classList.add('filter-change');
            setTimeout(() => {
                chartElement.classList.remove('filter-change');
            }, 500);
        }

        responseTimeChart.update();
    }

    // تحلیل سوالات دسته‌بندی
    function setupCategoryQuestionsAnalysis() {
        const analyzeBtn = document.getElementById('analyzeQuestionsBtn');
        const categorySelect = document.getElementById('categoryQuestionsFilter');
        const resultsContainer = document.getElementById('categoryQuestionsResults');
        const loadingContainer = document.getElementById('categoryQuestionsLoading');
        const errorContainer = document.getElementById('categoryQuestionsError');
        const errorMessage = document.getElementById('categoryQuestionsErrorMessage');

        if (!analyzeBtn || !categorySelect || !resultsContainer || !loadingContainer || !errorContainer) {
            console.warn("Category questions analysis elements not found");
            return;
        }

        analyzeBtn.addEventListener('click', function() {
            const category = categorySelect.value;
            if (!category) {
                errorContainer.classList.remove('d-none');
                errorMessage.textContent = 'لطفاً یک دسته‌بندی انتخاب کنید';
                return;
            }

            // نمایش بارگذاری
            resultsContainer.classList.add('d-none');
            errorContainer.classList.add('d-none');
            loadingContainer.classList.remove('d-none');

            // درخواست تحلیل سوالات
            fetch(`/admin/analytics/category_questions/${category}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`خطای سرور: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        // نمایش نتایج
                        displayCategoryQuestionsAnalysis(data);
                        loadingContainer.classList.add('d-none');
                        resultsContainer.classList.remove('d-none');
                    } else {
                        throw new Error(data.error || 'خطای نامشخص');
                    }
                })
                .catch(error => {
                    console.error("Error fetching category questions analysis:", error);
                    loadingContainer.classList.add('d-none');
                    errorContainer.classList.remove('d-none');
                    errorMessage.textContent = error.message;
                });
        });
    }

    // نمایش نتایج تحلیل سوالات
    function displayCategoryQuestionsAnalysis(data) {
        // 1. نمودار نرخ پاسخ صحیح به سوالات
        updateQuestionsSuccessRateChart(data.questions_analysis);

        // 2. لیست سوالات مشکل‌دار
        const problematicList = document.getElementById('problematicQuestionsList');
        if (problematicList) {
            problematicList.innerHTML = '';

            const problematicQuestions = data.questions_analysis.filter(q => q.success_rate < 40);
            if (problematicQuestions.length > 0) {
                problematicQuestions.forEach(question => {
                    const item = document.createElement('div');
                    item.className = 'list-group-item bg-dark text-light border-secondary';
                    item.innerHTML = `
                        <p class="mb-1">${question.question_text}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <small>پاسخ صحیح: ${question.correct_answer}</small>
                            <span class="badge bg-danger">${question.success_rate.toFixed(1)}%</span>
                        </div>
                    `;
                    problematicList.appendChild(item);
                });
            } else {
                problematicList.innerHTML = '<div class="list-group-item bg-dark text-light border-secondary">هیچ سوال مشکل‌داری یافت نشد</div>';
            }
        }

        // 3. لیست سوالات با بیشترین اشتباه
        const mostWrongList = document.getElementById('mostWrongQuestionsList');
        if (mostWrongList) {
            mostWrongList.innerHTML = '';

            // مرتب‌سازی بر اساس تعداد پاسخ نادرست
            const sortedQuestions = [...data.questions_analysis]
                .sort((a, b) => (b.answers_count - b.correct_count) - (a.answers_count - a.correct_count))
                .slice(0, 5);

            if (sortedQuestions.length > 0) {
                sortedQuestions.forEach(question => {
                    const wrongCount = question.answers_count - question.correct_count;
                    const item = document.createElement('div');
                    item.className = 'list-group-item bg-dark text-light border-secondary';
                    item.innerHTML = `
                        <p class="mb-1">${question.question_text}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <small>پاسخ صحیح: ${question.correct_answer}</small>
                            <span class="badge bg-warning text-dark">${wrongCount} پاسخ نادرست</span>
                        </div>
                    `;
                    mostWrongList.appendChild(item);
                });
            } else {
                mostWrongList.innerHTML = '<div class="list-group-item bg-dark text-light border-secondary">داده‌ای یافت نشد</div>';
            }
        }

        // 4. جدول تحلیل همه سوالات
        const tableBody = document.querySelector('#questionsAnalysisTable tbody');
        if (tableBody) {
            tableBody.innerHTML = '';

            data.questions_analysis.forEach(question => {
                const row = document.createElement('tr');

                // ساخت لیست گزینه‌های نادرست پرتکرار
                let wrongOptionsHTML = '';
                if (question.top_wrong_options && question.top_wrong_options.length > 0) {
                    wrongOptionsHTML = question.top_wrong_options
                        .map(option => `<span class="badge bg-secondary me-1">${option[0]} (${option[1]})</span>`)
                        .join(' ');
                } else {
                    wrongOptionsHTML = '<span class="text-muted">داده‌ای وجود ندارد</span>';
                }

                // تعیین رنگ نرخ موفقیت
                let successRateClass = 'bg-success';
                if (question.success_rate < 40) {
                    successRateClass = 'bg-danger';
                } else if (question.success_rate < 70) {
                    successRateClass = 'bg-warning text-dark';
                }

                row.innerHTML = `
                    <td>${question.question_text}</td>
                    <td>${question.answers_count}</td>
                    <td>${question.correct_count}</td>
                    <td><span class="badge ${successRateClass}">${question.success_rate.toFixed(1)}%</span></td>
                    <td>${wrongOptionsHTML}</td>
                `;

                tableBody.appendChild(row);
            });
        }
    }

    // نمودار نرخ پاسخ صحیح به سوالات
    function updateQuestionsSuccessRateChart(questionsData) {
        const ctx = document.getElementById('questionsSuccessRateChart');
        if (!ctx) return;

        // اگر نمودار قبلاً ایجاد شده، آن را نابود کنیم
        if (questionsSuccessRateChart) {
            questionsSuccessRateChart.destroy();
        }

        // محدود کردن تعداد سوالات برای نمایش بهتر (۱۰ سوال)
        let displayData = [...questionsData];
        if (displayData.length > 10) {
            displayData = displayData.slice(0, 10);
        }

        // کوتاه کردن متن سوالات برای نمایش بهتر
        const labels = displayData.map(q => {
            let text = q.question_text;
            return text.length > 40 ? text.substring(0, 37) + '...' : text;
        });

        const successRates = displayData.map(q => q.success_rate);

        // تعیین رنگ‌ها بر اساس نرخ موفقیت
        const backgroundColors = successRates.map(rate => {
            if (rate < 40) return colors.red;
            if (rate < 70) return colors.yellow;
            return colors.green;
        });

        // ایجاد نمودار جدید
        questionsSuccessRateChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'نرخ پاسخ صحیح (%)',
                    data: successRates,
                    backgroundColor: backgroundColors,
                    borderColor: backgroundColors.map(color => color.replace('0.7', '1')),
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                aspectRatio: 2,
                indexAxis: 'y',  // نمودار افقی
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(40, 42, 54, 0.8)',
                        titleColor: '#8be9fd',
                        bodyColor: '#f8f8f2',
                        bodyFont: {
                            family: 'Vazir, sans-serif'
                        },
                        titleFont: {
                            family: 'Vazir, sans-serif'
                        },
                        callbacks: {
                            title: function(tooltipItems) {
                                const index = tooltipItems[0].dataIndex;
                                return displayData[index].question_text;
                            },
                            label: function(context) {
                                const index = context.dataIndex;
                                return [
                                    `نرخ موفقیت: ${context.raw.toFixed(1)}%`,
                                    `تعداد پاسخ: ${displayData[index].answers_count}`,
                                    `پاسخ صحیح: ${displayData[index].correct_answer}`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        grid: {
                            color: 'rgba(98, 114, 164, 0.2)'
                        },
                        ticks: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 11
                            }
                        }
                    },
                    x: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: 'rgba(98, 114, 164, 0.2)'
                        },
                        ticks: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 12
                            }
                        }
                    }
                }
            }
        });
    }

    // تابع دریافت و نمایش توزیع سختی سوالات
    async function fetchAndDisplayQuestionDifficultyDistribution(category) {
        try {
            // نمایش وضعیت بارگذاری
            const chartContainer = document.getElementById('questionDifficultyDistributionChart').parentNode;

            if (chartContainer) {
                chartContainer.classList.add('loading');
                chartContainer.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">در حال بارگذاری...</p></div>';
            }

            // درخواست داده‌های توزیع سختی سوالات
            const response = await fetch(`/admin/analytics/question_difficulty_distribution/${category}`);

            if (!response.ok) {
                throw new Error(`خطای سرور: ${response.status}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'خطای نامشخص');
            }

            // ایجاد مجدد المان canvas
            chartContainer.innerHTML = '<canvas id="questionDifficultyDistributionChart" height="300"></canvas>';
            chartContainer.classList.remove('loading');

            // نمایش نمودار توزیع سختی سوالات
            displayQuestionDifficultyDistribution(data);

        } catch (error) {
            console.error("Error fetching question difficulty distribution:", error);

            const chartContainer = document.getElementById('questionDifficultyDistributionChart').parentNode;
            if (chartContainer) {
                chartContainer.classList.remove('loading');
                chartContainer.innerHTML = `
                    <div class="alert alert-danger text-center">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        خطا در دریافت داده‌ها: ${error.message}
                    </div>
                    <canvas id="questionDifficultyDistributionChart" height="300"></canvas>
                `;
            }
        }
    }

    // تابع نمایش نمودار توزیع سختی سوالات
    function displayQuestionDifficultyDistribution(data) {
        const ctx = document.getElementById('questionDifficultyDistributionChart');
        if (!ctx) return;

        // اگر نمودار قبلاً ایجاد شده، آن را نابود کنیم
        if (questionDifficultyDistributionChart) {
            questionDifficultyDistributionChart.destroy();
        }

        const categoryName = data.category === 'all' ? 'همه دسته‌بندی‌ها' : data.category;

        // ایجاد نمودار جدید
        questionDifficultyDistributionChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['آسان', 'متوسط', 'سخت'],
                datasets: [{
                    label: `تعداد سوالات بر اساس سختی (${categoryName})`,
                    data: [data.easy_count, data.medium_count, data.hard_count],
                    backgroundColor: [colors.green, colors.yellow, colors.red],
                    borderColor: [colors.green, colors.yellow, colors.red],
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 14
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(40, 42, 54, 0.8)',
                        titleColor: '#8be9fd',
                        bodyColor: '#f8f8f2',
                        bodyFont: {
                            family: 'Vazir, sans-serif'
                        },
                        titleFont: {
                            family: 'Vazir, sans-serif'
                        },
                        callbacks: {
                            label: function(context) {
                                return `تعداد سوالات: ${context.raw}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(98, 114, 164, 0.2)'
                        },
                        ticks: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 12
                            }
                        },
                        title: {
                            display: true,
                            text: 'تعداد سوالات',
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 14
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(98, 114, 164, 0.2)'
                        },
                        ticks: {
                            color: '#f8f8f2',
                            font: {
                                family: 'Vazir, sans-serif',
                                size: 12
                            }
                        }
                    }
                }
            }
        });
    }

    // اصلاح اندازه و تناسب نمودارها
    function adjustChartSizes() {
        // تنظیم رنگ نمودار دسته‌بندی‌ها و کاربران
        if (categoryChart) {
            categoryChart.options.aspectRatio = 1.5;
            categoryChart.update();
        }

        if (userPerformanceChart) {
            userPerformanceChart.options.aspectRatio = 1.5;
            userPerformanceChart.update();
        }
    }

    // ایجاد همه نمودارها
    function initAllCharts() {
        console.log("Initializing all charts");
        initTimePerformanceChart();
        initTimeChart();
        initCategoryChart();
        initUserPerformanceChart();
        initDifficultyChart();
    }

    // راه‌اندازی همه قابلیت‌ها
    function initialize() {
        console.log("Initializing analytics module");

        // ایجاد نمودارها
        initAllCharts();

        // ایجاد نمودارهای جدید
        initCategoryRadarChart();
        initResponseTimeChart();

        // بهبود نمودار سطح دشواری
        enhanceDifficultyChart();

        // راه‌اندازی تحلیل سوالات دسته‌بندی
        setupCategoryQuestionsAnalysis();

        // تنظیم رویدادها
        setupFilterEventListeners();
        setupDownloadButton();

        // فراخوانی تابع تنظیم اندازه نمودارها
        adjustChartSizes();


        updateCategoryRadarChart('all');


        updateResponseTimeChart('all')

        // فراخوانی تابع دریافت توزیع سختی سوالات برای همه دسته‌بندی‌ها
        // به تعویق انداختن فراخوانی برای اطمینان از آماده بودن صفحه
        setTimeout(() => {
            fetchAndDisplayQuestionDifficultyDistribution('all');
        }, 1000);

        console.log("Analytics initialization complete");
    }

    // شروع راه‌اندازی
    initialize();
});