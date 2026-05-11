<template>
  <div class="flex flex-col min-h-screen w-full relative">
    <div class="mesh-bg"><div class="blob blob-1"></div><div class="blob blob-2"></div><div class="blob blob-3"></div></div>

    <!-- Loading Overlay -->
    <div v-show="loading" id="loading-overlay" class="fixed inset-0 flex flex-col items-center justify-center">
        <div class="loader mb-4"></div>
        <h2 class="text-xl font-bold">{{ lang === 'zh' ? '处理矩阵中...' : 'Processing Matrix...' }}</h2>
        <p class="text-white/60 text-sm mt-2" id="loading-text">{{ lang === 'zh' ? '正在请求 Python RMT 引擎' : 'Requesting Python RMT Engine' }}</p>
    </div>

    <!-- Navigation -->
    <nav class="w-full px-4 sm:px-8 py-4 sm:py-6 flex justify-between items-center z-10">
        <div class="flex items-center gap-2 sm:gap-3">
            <div class="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-gradient-to-tr from-iosBlue to-purple-500 flex items-center justify-center font-bold text-sm">R</div>
            <span class="text-lg sm:text-xl font-semibold tracking-tight text-white/90">
                {{ lang === 'zh' ? '随机矩阵分析' : 'RMT Analytics' }}
            </span>
        </div>
        <div class="flex items-center gap-2 sm:gap-4">
            <!-- Language Toggle -->
            <div class="flex items-center gap-1 bg-black/30 rounded-full p-1 border border-white/10 scale-90 sm:scale-100">
                <button @click="lang = 'zh'" :class="lang === 'zh' ? 'bg-white/20 text-white shadow rounded-full px-2 sm:px-3 py-1 text-xs transition' : 'text-white/50 hover:text-white px-2 sm:px-3 py-1 text-xs transition'">中</button>
                <button @click="lang = 'en'" :class="lang === 'en' ? 'bg-white/20 text-white shadow rounded-full px-2 sm:px-3 py-1 text-xs transition' : 'text-white/50 hover:text-white px-2 sm:px-3 py-1 text-xs transition'">EN</button>
            </div>
            
            <button @click="rmtChartRef?.exportChart()" class="glass-panel px-3 sm:px-6 py-2 text-sm font-medium hover:bg-white/10 transition duration-300 flex items-center gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                <span class="hidden sm:inline">{{ lang === 'zh' ? '导出图表' : 'Export Chart' }}</span>
            </button>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="flex-grow px-4 lg:px-8 pb-8 lg:pb-12 grid grid-cols-1 lg:grid-cols-12 gap-6 z-10 w-full 3xl:max-w-[2000px] 3xl:mx-auto">
        
        <!-- Left Column: Controls & Upload -->
        <div class="lg:col-span-4 xl:col-span-3 flex flex-col gap-6">
            
            <!-- Real Upload Area (Trigger File Input) -->
            <div class="glass-panel p-6 flex flex-col items-center justify-center text-center transition group border-dashed border-2 border-white/20 relative">
                <div @click="triggerUpload" class="w-full h-full cursor-pointer flex flex-col items-center">
                    <input type="file" ref="fileInput" accept=".csv" class="hidden" @click.stop @change="handleFileUpload">
                    <svg class="w-12 h-12 text-white/60 mb-4 group-hover:text-iosBlue transition" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
                    <h3 class="font-medium text-lg text-white">{{ lang === 'zh' ? '上传真实矩阵数据' : 'Upload Real Matrix' }}</h3>
                    <p class="text-white/50 text-xs mt-2">{{ lang === 'zh' ? 'CSV 格式 (列=特征)' : 'CSV Format (Columns=Features)' }}</p>
                </div>

                <!-- Example Dataset Quick Link -->
                <div class="mt-6 pt-6 border-t border-white/10 w-full">
                    <button @click="showExamples = !showExamples" class="w-full flex items-center justify-center gap-2 py-2 px-4 bg-white/5 hover:bg-white/10 rounded-xl text-sm text-iosBlue transition">
                        <span>✨ {{ lang === 'zh' ? '使用预置测试集' : 'Use Test Dataset' }}</span>
                        <svg class="w-4 h-4 transition-transform" :class="{'rotate-180': showExamples}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                    </button>
                    
                    <div v-if="showExamples" class="mt-3 space-y-2 max-h-[200px] overflow-y-auto pr-1 custom-scrollbar">
                        <div v-for="ex in exampleList" :key="ex" 
                             @click="loadExample(ex)"
                             class="text-left px-3 py-2 bg-black/20 hover:bg-iosBlue/20 rounded-lg text-xs text-white/70 hover:text-white cursor-pointer transition-colors border border-white/5">
                             📄 {{ ex.replace('.csv', '') }}
                        </div>
                        <div v-if="exampleList.length === 0" class="text-xs text-white/30 italic py-2">{{ lang === 'zh' ? '未找到测试集...' : 'No test sets found...' }}</div>
                    </div>
                </div>
            </div>

            <!-- Model Switcher -->
            <div class="glass-panel p-2 flex bg-black/20 rounded-full mx-2">
                <button @click="switchModel('MP')" :class="currentModel === 'MP' ? 'flex-1 py-2 text-sm font-medium rounded-full bg-white/20 shadow text-white transition' : 'flex-1 py-2 text-sm font-medium rounded-full text-white/60 hover:text-white transition'">{{ lang === 'zh' ? 'M-P 分布' : 'M-P' }}</button>
                <button @click="switchModel('WIGNER')" :class="currentModel === 'WIGNER' ? 'flex-1 py-2 text-sm font-medium rounded-full bg-white/20 shadow text-white transition' : 'flex-1 py-2 text-sm font-medium rounded-full text-white/60 hover:text-white transition'">{{ lang === 'zh' ? 'Wigner 半圆' : 'Wigner' }}</button>
            </div>

            <!-- Parameters Panel -->
            <div class="glass-panel p-6">
                <div class="flex justify-between items-center mb-6">
                    <h3 class="font-semibold text-lg flex items-center gap-2">
                        <svg class="w-5 h-5 text-iosBlue" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path></svg>
                        {{ lang === 'zh' ? '参数设置' : 'Params' }}
                    </h3>
                </div>
                
                <div class="space-y-6">
                    <!-- Ratio q -->
                    <div :style="{ opacity: currentModel === 'MP' ? '1' : '0.3' }">
                        <div class="flex justify-between text-sm mb-2 text-white/80">
                            <span title="Ratio of dimensions (p/n)">{{ lang === 'zh' ? '维度比例 (q = p/n)' : 'Dim Ratio (q = p/n)' }}</span>
                            <span class="font-mono text-iosBlue">{{ q.toFixed(2) }}</span>
                        </div>
                        <input type="range" v-model.number="q" min="0.1" max="2.0" step="0.01" :disabled="currentModel !== 'MP'" @change="fetchData" @input="debouncedFetch">
                    </div>

                    <!-- Variance -->
                    <div>
                        <div class="flex justify-between text-sm mb-2 text-white/80">
                            <span>{{ lang === 'zh' ? '方差 (σ²)' : 'Variance (σ²)' }}</span>
                            <span class="font-mono text-iosBlue">{{ sigmaSq.toFixed(2) }}</span>
                        </div>
                        <input type="range" v-model.number="sigmaSq" min="0.1" max="3.0" step="0.05" @change="fetchData" @input="debouncedFetch">
                    </div>
                    
                    <!-- Bins -->
                    <div>
                        <div class="flex justify-between text-sm mb-2 text-white/80">
                            <span>{{ lang === 'zh' ? '直方图分箱数 (Bins)' : 'Histogram Bins' }}</span>
                            <span class="font-mono text-iosBlue">{{ bins }}</span>
                        </div>
                        <input type="range" v-model.number="bins" min="10" max="100" step="5">
                    </div>

                    <!-- Preprocessing -->
                    <div :style="{ opacity: currentModel === 'MP' ? '1' : '0.3' }">
                        <div class="flex justify-between text-sm mb-2 text-white/80">
                            <span>{{ lang === 'zh' ? '数据预处理方式 (CSV)' : 'Data Preprocessing (CSV)' }}</span>
                        </div>
                        <div class="flex bg-black/20 rounded-lg p-1 border border-white/10">
                            <button @click="useStandardization = true; reprocessFile()" :disabled="currentModel !== 'MP'" :class="useStandardization ? 'flex-1 bg-white/20 text-white shadow rounded p-1 text-sm' : 'flex-1 text-white/50 hover:text-white p-1 text-sm transition'">{{ lang === 'zh' ? '标准化' : 'Standardized' }}</button>
                            <button @click="useStandardization = false; reprocessFile()" :disabled="currentModel !== 'MP'" :class="!useStandardization ? 'flex-1 bg-white/20 text-white shadow rounded p-1 text-sm' : 'flex-1 text-white/50 hover:text-white p-1 text-sm transition'">{{ lang === 'zh' ? '原始协方差' : 'Raw Covariance' }}</button>
                        </div>
                    </div>

                    <!-- Fill Strategy (Upload only) -->
                    <div :style="{ opacity: currentModel === 'MP' ? '1' : '0.3' }">
                        <div class="flex justify-between text-sm mb-2 text-white/80">
                            <span>{{ lang === 'zh' ? '缺失值(NaN)填充策略' : 'NaN Fill Strategy (CSV Upload)' }}</span>
                        </div>
                        <select v-model="fillStrategy" @change="reprocessFile()" :disabled="currentModel !== 'MP'" class="w-full bg-[#1c1c1e] bg-opacity-80 border border-white/20 text-white text-sm rounded-lg p-2 focus:outline-none">
                            <option value="zero">{{ lang === 'zh' ? '用零填充' : 'Fill with Zeroes' }}</option>
                            <option value="mean">{{ lang === 'zh' ? '列均值填充' : 'Column Mean' }}</option>
                            <option value="drop">{{ lang === 'zh' ? '删除含缺失值的行' : 'Drop NaN Rows' }}</option>
                        </select>
                    </div>

                    <!-- Normalization -->
                    <div>
                        <div class="flex justify-between text-sm mb-2 text-white/80">
                            <span>{{ lang === 'zh' ? '归一化方式' : 'Normalization' }}</span>
                        </div>
                        <div class="flex bg-black/20 rounded-lg p-1 border border-white/10">
                            <button @click="normType = 'density'" :class="normType === 'density' ? 'flex-1 bg-white/20 text-white shadow rounded p-1 text-sm' : 'flex-1 text-white/50 hover:text-white p-1 text-sm transition'">{{ lang === 'zh' ? '概率密度' : 'Density' }}</button>
                            <button @click="normType = 'count'" :class="normType === 'count' ? 'flex-1 bg-white/20 text-white shadow rounded p-1 text-sm' : 'flex-1 text-white/50 hover:text-white p-1 text-sm transition'">{{ lang === 'zh' ? '频数计算' : 'Count' }}</button>
                        </div>
                    </div>

                    <!-- Time Range (Rolling Window) Slider -->
                    <div v-if="currentDataset && dsHasFileConfigured() && isTimeScaleActive" class="pt-2">
                        <div class="flex justify-between text-sm mb-2 text-white/80">
                            <span title="Select time window range of the dataset">{{ lang === 'zh' ? '时间窗口 (行)' : 'Time Window (Rows)' }}</span>
                            <span class="font-mono text-iosBlue">{{ formatTooltip(rowRange[0]) }} - {{ formatTooltip(rowRange[1]) }}</span>
                        </div>
                        <el-slider 
                            v-model="rowRange" 
                            range 
                            :min="0" 
                            :max="maxRows" 
                            :format-tooltip="formatTooltip"
                            @change="handleSliderChange"
                            class="custom-slider" 
                        />
                    </div>

                    <!-- Theory Upper Bound -->
                    <div class="pt-4 border-t border-white/10">
                        <div class="flex justify-between items-center text-sm">
                            <span class="text-white/60">{{ lang === 'zh' ? '理论上限 (Theory Upper Bound)' : 'Theory Upper Bound' }}</span>
                            <span class="font-mono text-iosRed font-bold bg-iosRed/20 px-2 py-1 rounded">{{ lambdaPlus.toFixed(3) }}</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Anomaly Insights -->
            <div class="glass-panel p-6 flex-grow flex flex-col min-h-[250px]">
                <h3 class="font-semibold text-lg mb-2 text-iosOrange flex justify-between">
                    {{ lang === 'zh' ? '异常信号因子' : 'Signal Factors' }}
                    <span class="text-xs bg-iosOrange/20 px-2 py-1 rounded">{{ anomalies.length }} {{ lang === 'zh' ? '个' : 'found' }}</span>
                </h3>
                
                <!-- Domain Selector -->
                <div class="mb-3">
                    <select v-model="selectedDomain" class="w-full bg-[#1c1c1e] bg-opacity-80 border border-white/20 text-white/80 text-xs rounded p-1 focus:outline-none">
                        <option value="general">{{ lang === 'zh' ? '通用模型 (统计主成分)' : 'General (Principal Components)' }}</option>
                        <option value="finance">{{ lang === 'zh' ? '金融市场 (股票宏观面)' : 'Finance (Market Mode)' }}</option>
                        <option value="environment">{{ lang === 'zh' ? '环境监测 (突发污染源)' : 'Environment (Pollution Events)' }}</option>
                        <option value="neuro">{{ lang === 'zh' ? '神经科学 (大脑网络同步)' : 'Neuroscience (Network Sync)' }}</option>
                    </select>
                </div>

                <div class="text-xs text-white/60 p-2 bg-black/20 rounded mb-4">
                    <div v-if="selectedDomain === 'finance'">
                        <span class="text-iosOrange">{{ lang === 'zh' ? '金融意义：' : 'Finance:' }}</span> {{ lang === 'zh' ? '超出理论边界的最大特征值通常代表着“市场模式(Market Mode)”或系统性风险，即整个大盘共同受到的宏观因素影响。次大的异常特征值代表行业板块效应。' : 'The largest eigenvalues exceeding the bound represent the "Market Mode" or systemic risk, reflecting macro factors affecting the entire market. Subsequent outliers represent sector effects.' }}
                    </div>
                    <div v-else-if="selectedDomain === 'environment'">
                        <span class="text-iosOrange">{{ lang === 'zh' ? '环境意义：' : 'Environment:' }}</span> {{ lang === 'zh' ? '异常特征值通常代表了突发的区域性极端事件（如沙尘暴、大规模工业泄漏等），反映多个监测站同时监测到的强烈异常污染信号。' : 'Outliers represent sudden regional extreme events (e.g., sandstorms, major industrial leaks), reflecting strong anomalous signals detected simultaneously by multiple stations.' }}
                    </div>
                    <div v-else-if="selectedDomain === 'neuro'">
                        <span class="text-iosOrange">{{ lang === 'zh' ? '神经科学意义：' : 'Neuroscience:' }}</span> {{ lang === 'zh' ? '这些特征值往往对应大脑网络在执行特定认知任务时的大规模同步激活区域或主导的神经元活动模式。' : 'These eigenvalues often correspond to large-scale synchronized activation regions or dominant neural activity patterns during specific cognitive tasks.' }}
                    </div>
                    <div v-else>
                        <span class="text-iosOrange">{{ lang === 'zh' ? '统计意义：' : 'Statistics:' }}</span> {{ lang === 'zh' ? '偏离主体理论分布的特征值表示数据中存在着非随机的“真实信号”，它们主导着整个数据矩阵的协方差结构。' : 'Eigenvalues deviating from the bulk distribution indicate the presence of non-random "true signals" governing the covariance structure.' }}
                    </div>
                </div>

                <div class="space-y-2 overflow-y-auto pr-2 flex-grow custom-scrollbar">
                    <p v-if="anomalies.length === 0" class="text-sm text-white/40 text-center mt-4">{{ lang === 'zh' ? '未检测到显著异常信号。' : 'No significant signals detected.' }}</p>
                    <div v-else v-for="(val, index) in anomalies" :key="index"
                         :id="'anomaly-' + index"
                         class="rounded-lg border overflow-hidden transition-all duration-300"
                         :class="expandedEigenvector === index 
                           ? 'bg-white/10 border-iosOrange/40 shadow-[0_0_12px_rgba(255,159,10,0.15)]' 
                           : 'bg-white/5 border-white/10 hover:bg-white/10'">
                        <!-- Eigenvalue Row (clickable to expand) -->
                        <div class="flex items-center justify-between p-2 cursor-pointer select-none group" @click="toggleEigenvectorDetail(index)">
                            <div class="flex items-center gap-2">
                                <svg class="w-3 h-3 text-white/40 transition-transform duration-300 ease-out" :class="{'rotate-90': expandedEigenvector === index}" fill="currentColor" viewBox="0 0 20 20"><path d="M6 6l8 4-8 4V6z"/></svg>
                                <span class="text-white/80 text-sm font-mono">λ_{{ index + 1 }}</span>
                                <!-- Pulsing indicator when expanded -->
                                <span v-if="expandedEigenvector === index" class="w-1.5 h-1.5 rounded-full bg-iosOrange animate-pulse"></span>
                            </div>
                            <span class="font-mono text-iosOrange font-bold group-hover:scale-105 transition-transform">{{ val.toFixed(4) }}</span>
                        </div>
                        <!-- Expanded Eigenvector Detail Panel -->
                        <Transition name="eigvec-slide">
                        <div v-if="expandedEigenvector === index && getEigenvectorForAnomaly(index)" class="px-3 pb-3 pt-1 border-t border-white/10 bg-black/20">
                            <p class="text-[10px] text-white/40 mb-2 uppercase tracking-wider">{{ lang === 'zh' ? '特征向量成分权重 (Top-5)' : 'Eigenvector Component Weights (Top-5)' }}</p>
                            <div class="space-y-1.5">
                                 <div v-for="(comp, ci) in getEigenvectorForAnomaly(index).top_components" :key="ci" 
                                      class="flex items-center gap-2 eigvec-bar-enter"
                                      :style="{ animationDelay: (Number(ci) * 80) + 'ms' }">
                                     <span class="text-[11px] text-white/70 w-[90px] truncate shrink-0" :title="comp.column_name">{{ comp.column_name }}</span>
                                     <div class="flex-1 h-4 bg-black/30 rounded-sm relative overflow-hidden">
                                         <div class="absolute top-0 left-0 h-full rounded-sm eigvec-bar-fill"
                                              :class="comp.weight >= 0 ? 'bg-gradient-to-r from-emerald-500/80 to-emerald-400/60' : 'bg-gradient-to-r from-rose-500/80 to-rose-400/60'"
                                              :style="{ '--target-width': (comp.abs_weight / (getMaxWeight(index) || 1) * 100) + '%', animationDelay: (Number(ci) * 80 + 100) + 'ms' }">
                                         </div>
                                        <span class="absolute inset-0 flex items-center justify-end pr-1 text-[9px] font-mono text-white/60">
                                            {{ comp.weight >= 0 ? '+' : '' }}{{ comp.weight.toFixed(3) }}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <div class="mt-2 flex gap-3 text-[9px] text-white/30">
                                <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-sm bg-emerald-500/80"></span>{{ lang === 'zh' ? '正相关' : 'Positive' }}</span>
                                <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-sm bg-rose-500/80"></span>{{ lang === 'zh' ? '负相关' : 'Negative' }}</span>
                            </div>
                        </div>
                        </Transition>
                    </div>
                </div>
            </div>

        </div>

        <!-- Right Column: Visualization -->
        <div class="lg:col-span-8 xl:col-span-9 glass-panel p-2 flex flex-col relative overflow-hidden min-h-[600px] lg:h-[calc(100vh-140px)] lg:sticky lg:top-8">
            
            <!-- Liquid Glass Switcher -->
            <div class="relative lg:absolute top-0 lg:top-4 left-0 lg:left-1/2 lg:transform lg:-translate-x-1/2 z-30 flex flex-wrap justify-center bg-black/40 backdrop-blur-xl border border-white/10 p-1 rounded-2xl lg:rounded-full shadow-[0_4px_30px_rgba(0,0,0,0.5)] mb-4 lg:mb-0 mx-2 lg:mx-0">
                <button @click="currentView = 'spectrum'" :class="currentView === 'spectrum' ? 'bg-white/20 shadow-md text-white' : 'text-white/50 hover:text-white'" class="flex-1 lg:flex-none px-3 lg:px-4 py-1.5 rounded-xl lg:rounded-full text-xs lg:text-sm font-medium transition-all duration-300">{{ lang === 'zh' ? '光谱' : 'Spectrum' }}</button>
                <button @click="currentView = 'ipr'" :class="currentView === 'ipr' ? 'bg-white/20 shadow-md text-white' : 'text-white/50 hover:text-white'" class="flex-1 lg:flex-none px-3 lg:px-4 py-1.5 rounded-xl lg:rounded-full text-xs lg:text-sm font-medium transition-all duration-300">{{ lang === 'zh' ? '局部化' : 'IPR' }}</button>
                <button @click="currentView = 'heatmap'" :class="currentView === 'heatmap' ? 'bg-white/20 shadow-md text-white' : 'text-white/50 hover:text-white'" class="flex-1 lg:flex-none px-3 lg:px-4 py-1.5 rounded-xl lg:rounded-full text-xs lg:text-sm font-medium transition-all duration-300">{{ lang === 'zh' ? '矩阵' : 'Heatmap' }}</button>
                <button @click="currentView = 'rolling'" :class="currentView === 'rolling' ? 'bg-white/20 shadow-md text-white' : 'text-white/50 hover:text-white'" class="flex-1 lg:flex-none px-3 lg:px-4 py-1.5 rounded-xl lg:rounded-full text-xs lg:text-sm font-medium transition-all duration-300">{{ lang === 'zh' ? '演化' : 'Rolling' }}</button>
            </div>

            <div class="relative lg:absolute top-0 lg:top-4 left-0 lg:left-6 z-10 px-4 lg:px-0 flex flex-col gap-1 sm:gap-2">
                <div class="flex flex-col sm:flex-row sm:items-center pointer-events-auto gap-2">
                    <h2 class="text-xl sm:text-2xl font-bold tracking-tight">
                        {{ currentModel === 'MP' ? (lang === 'zh' ? 'M-P 谱分布' : 'M-P Spectrum') : (lang === 'zh' ? 'Wigner 半圆律' : 'Wigner Semicircle') }}
                    </h2>
                    <!-- Custom Apple-style Dropdown -->
                    <div v-if="uploadedDatasets.length > 0" class="relative flex items-center">
                        <button @click="toggleDropdown" 
                                class="flex items-center justify-between px-3 sm:px-4 py-1.5 bg-black/30 backdrop-blur-xl hover:bg-white/10 text-white/90 text-xs sm:text-sm rounded-full border border-white/10 font-medium tracking-tight focus:outline-none focus:ring-1 focus:ring-iosBlue/50 cursor-pointer transition-all shadow-sm w-full sm:w-[240px]"
                                :title="lang === 'zh' ? '选择数据集' : 'Select Dataset'">
                            <span class="truncate">{{ currentDataset || (lang === 'zh' ? '模拟生成中心...' : 'Simulation Hub...') }}</span>
                            <svg class="w-3 h-3 ml-2 text-white/50 shrink-0 transition-transform duration-200" :class="{'rotate-180': isDropdownOpen}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                        </button>

                        <div v-if="isDropdownOpen" @click="closeDropdown" class="fixed inset-0 z-40"></div>
                        <div v-if="isDropdownOpen" class="absolute top-10 left-0 w-[240px] z-50 bg-[#1c1c1e]/90 backdrop-blur-3xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col p-1.5">
                            <div class="max-h-[240px] overflow-y-auto pr-1 custom-scrollbar">
                                <div @click="selectDataset('')" class="px-3 py-2 text-sm text-white/60 hover:bg-white/10 rounded-xl cursor-pointer flex items-center gap-2 mb-1">
                                     <div class="w-2 h-2 rounded-full" :class="!currentDataset ? 'bg-iosBlue' : 'bg-transparent border border-white/30'"></div>
                                     {{ lang === 'zh' ? '模拟生成中心...' : 'Simulation Hub...' }}
                                </div>
                                <div class="h-px bg-white/10 mx-2 mb-1"></div>
                                <div v-for="ds in uploadedDatasets" :key="ds.name" @click="selectDataset(ds.name)" class="px-3 py-2 text-sm text-white/90 hover:bg-white/10 rounded-xl cursor-pointer transition-colors flex flex-col gap-0.5 group relative">
                                    <div class="flex items-center justify-between">
                                        <div class="flex items-center gap-2 overflow-hidden pr-2">
                                            <div class="w-2 h-2 rounded-full shrink-0" :class="currentDataset === ds.name ? 'bg-iosGreen' : 'bg-transparent border border-white/30'"></div>
                                            <span class="font-medium truncate">{{ ds.name }}</span>
                                        </div>
                                        <button @click="(e) => deleteDataset(ds.name, e)" class="opacity-0 group-hover:opacity-100 absolute right-2 p-1 hover:bg-white/20 rounded text-white/40 hover:text-iosRed transition-all">
                                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                                        </button>
                                    </div>
                                    <span class="text-xs text-white/40 font-mono ml-4">q={{ ds.q.toFixed(2) }} | {{ ds.p }}x{{ ds.n }}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <p class="text-white/50 text-sm hidden sm:block">{{ lang === 'zh' ? '经验特征值分布 vs. 理论概率密度' : 'Empirical Distribution vs. Theoretical Density' }}</p>
            </div>
            
            <!-- Spectrum View -->
            <div v-show="currentView === 'spectrum'" class="flex-grow flex flex-col h-full w-full relative">
                <RmtChart 
                  ref="rmtChartRef"
                  v-if="eigenvalues.length > 0"
                  :model="currentModel"
                  :eigenvalues="eigenvalues"
                  :theoreticalCurve="theoreticalCurve"
                  :bins="bins"
                  :lambdaPlus="lambdaPlus"
                  :lambdaMinus="lambdaMinus"
                  :normType="normType"
                  :lang="lang"
                  :highlightAnomalyIndex="expandedEigenvector"
                  @anomalies="handleAnomalies"
                  @outlier-click="handleOutlierClick"
                />

                <!-- Eigenvector Full Chart -->
                <Transition name="eigvec-slide">
                  <div v-if="expandedEigenvector !== null && getEigenvectorForAnomaly(expandedEigenvector)" class="w-full mt-2 border border-white/10 relative bg-black/30 backdrop-blur-md rounded-2xl overflow-hidden shadow-lg z-10 shrink-0 mb-2">
                    <div class="px-4 py-2 flex justify-between items-center bg-white/5 border-b border-white/10">
                       <h3 class="text-sm font-bold text-white/80 font-mono">
                         {{ lang === 'zh' ? '特征向量 Loading (λ=' + getEigenvectorForAnomaly(expandedEigenvector).eigenvalue.toFixed(4) + ')' : 'Eigenvector Loading (λ=' + getEigenvectorForAnomaly(expandedEigenvector).eigenvalue.toFixed(4) + ')' }}
                       </h3>
                       <button @click="expandedEigenvector = null" class="text-white/40 hover:text-white transition p-1 rounded-full hover:bg-white/10">
                         <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                       </button>
                    </div>
                    <EigenvectorChart :eigenvector="getEigenvectorForAnomaly(expandedEigenvector)" :columnNames="columnNames" :lang="lang" />
                  </div>
                </Transition>
            </div>

            <!-- Other Views (IPR, Heatmap, Rolling) ... -->
             <div v-if="currentView === 'ipr'" class="flex-grow flex flex-col items-center justify-center h-full w-full relative pt-20 p-8">
                <h2 class="text-xl font-bold mb-2 text-white/80">{{ lang === 'zh' ? '逆参与率 (IPR) 局部化' : 'IPR Localization' }}</h2>
                <div class="w-full h-full bg-black/20 rounded-xl border border-white/10" id="ipr-chart-container">
                    <div ref="iprChartContainer" class="w-full h-full"></div>
                </div>
            </div>

            <div v-if="currentView === 'heatmap'" class="flex-grow flex flex-col items-center justify-center h-full w-full relative pt-20 p-8">
                <h2 class="text-xl font-bold mb-4 text-white/80">{{ lang === 'zh' ? 'RMT 降噪相关性矩阵' : 'RMT Cleaned Heatmap' }}</h2>
                <div v-if="getDatasetProperty('cleaned_heatmap_base64')" class="w-full flex flex-col items-center h-full min-h-0">
                    <img :src="(getDatasetProperty('cleaned_heatmap_base64') as string)" class="max-w-full max-h-full object-contain rounded-xl border border-white/10">
                </div>
                <div v-else class="text-white/40 italic">上传数据集后生成热力图。</div>
            </div>

            <!-- AI Sidebar Toggle -->
            <div class="absolute top-4 right-4 flex gap-2 z-20">
                <button @click="isAiSettingsOpen = true" class="p-1.5 bg-black/30 backdrop-blur border border-white/10 rounded-full text-white/50 hover:text-white shadow-sm">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path></svg>
                </button>
                <button @click="openAiDrawer" class="flex items-center gap-2 px-4 py-1.5 bg-gradient-to-r from-indigo-500/80 to-purple-600/80 text-white rounded-full text-sm font-medium shadow-lg transition-all">
                    <span>✨ {{ lang === 'zh' ? 'AI 洞察' : 'AI Insights' }}</span>
                </button>
            </div>
        </div>
    </main>

    <!-- AI Insights Drawer -->
    <div class="fixed top-0 right-0 bottom-0 w-full sm:w-[450px] bg-[#1c1c1e]/95 backdrop-blur-3xl border-l border-white/10 shadow-2xl z-50 transition-transform duration-300 transform flex flex-col"
         :class="isAiDrawerOpen ? 'translate-x-0' : 'translate-x-full'">
        <div class="p-5 border-b border-white/10 flex justify-between items-center bg-black/20">
            <h3 class="text-lg font-bold text-white flex items-center gap-2">✨ {{ lang === 'zh' ? '深度 AI 分析' : 'Deep AI Analysis' }}</h3>
            <button @click="isAiDrawerOpen = false" class="text-white/50 hover:text-white p-1 rounded-full bg-white/5 transition">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
        </div>
        <div class="flex-1 overflow-y-auto p-6 prose prose-invert prose-sm max-w-none custom-scrollbar" v-html="renderedMarkdown"></div>
        <div class="p-4 border-t border-white/10 bg-black/30">
            <button @click="generateReport" :disabled="isGenerating || !currentDataset" class="w-full py-3 rounded-xl font-medium transition-all shadow-lg flex justify-center items-center gap-2 bg-gradient-to-r from-indigo-500 to-purple-600 text-white disabled:opacity-30">
                <span v-if="!isGenerating">{{ lang === 'zh' ? '生成洞察报告' : 'Generate Insights' }}</span>
                <span v-else>分析中...</span>
            </button>
        </div>
    </div>
    
    <!-- AI Settings Modal -->
    <div v-if="isAiSettingsOpen" class="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
        <div class="bg-[#1c1c1e] border border-white/10 p-6 rounded-2xl w-full max-w-[400px] shadow-2xl transition-all">
            <h3 class="text-xl font-bold text-white mb-4">{{ lang === 'zh' ? 'AI 设置' : 'AI Settings' }}</h3>
            <div class="flex flex-col gap-4">
                <input v-model="aiSettings.baseUrl" type="text" class="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white text-sm" placeholder="API Base URL">
                <input v-model="aiSettings.apiKey" type="password" class="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white text-sm" placeholder="API Key">
                <input v-model="aiSettings.modelName" type="text" class="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white text-sm" placeholder="Model Name">
            </div>
            <button @click="isAiSettingsOpen = false" class="mt-6 w-full py-2 bg-iosBlue rounded-lg text-white font-medium">保存并关闭</button>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick, watch } from 'vue';
import { marked } from 'marked';
// @ts-ignore
import markedKatex from 'marked-katex-extension';
import 'katex/dist/katex.min.css';
import RmtChart from './components/RmtChart.vue';
import EigenvectorChart from './components/EigenvectorChart.vue';
import { fetchWignerData, fetchMPData, uploadMatrix, streamAnalyze, fetchRollingData, fetchExamples, useExample } from './api/rmt';
// @ts-ignore
import * as echarts from 'echarts';

marked.use(markedKatex({ throwOnError: false, nonStandard: true }));

// --- UI State ---
const lang = ref<'zh' | 'en'>('zh');
const loading = ref(false);
const showExamples = ref(false);
const exampleList = ref<string[]>([]);
const currentView = ref('spectrum');
const isAiSettingsOpen = ref(false);
const isAiDrawerOpen = ref(false);
const isGenerating = ref(false);
const aiReport = ref('');
const isDropdownOpen = ref(false);
const expandedEigenvector = ref<number | null>(null);

// --- RMT Parameters & Data ---
const currentModel = ref<'MP' | 'WIGNER'>('MP');
const q = ref(0.35);
const sigmaSq = ref(1.00);
const bins = ref(50);
const fillStrategy = ref('zero');
const useStandardization = ref(true);
const normType = ref<'density' | 'count'>('density');
const selectedDomain = ref('general');

const eigenvalues = ref<number[]>([]);
const theoreticalCurve = ref<{ x: number[], y: number[] } | null>(null);
const lambdaPlus = ref(0.0);
const lambdaMinus = ref(0.0);
const anomalies = ref<number[]>([]);

// --- Dataset Management ---
const currentDataset = ref<string>('');
const uploadedDatasets = ref<any[]>([]);
const maxRows = ref(100);
const rowRange = ref<[number, number]>([0, 100]);
const fileLinesCache = ref<string[]>([]);
const isTimeScaleActive = ref(false);

const aiSettings = ref({
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    apiKey: '',
    modelName: 'qwen-plus'
});

const rmtChartRef = ref<any>(null);
const fileInput = ref<HTMLInputElement | null>(null);
const iprChartContainer = ref<HTMLElement | null>(null);

// --- Functions ---
const loadExampleList = async () => {
    try { exampleList.value = await fetchExamples(); } 
    catch (e) { console.error("Example list error", e); }
};

const loadExample = async (name: string) => {
    loading.value = true;
    showExamples.value = false;
    currentModel.value = 'MP';
    currentDataset.value = name;
    try {
        const data = await useExample(name, Math.sqrt(sigmaSq.value), fillStrategy.value, useStandardization.value);
        updateDataWithResponse(name, data);
        fileLinesCache.value = [];
        maxRows.value = data.n;
        rowRange.value = [0, data.n];
        isTimeScaleActive.value = false;
    } catch (err: any) {
        alert("Load Error: " + err.message);
    } finally { loading.value = false; }
};

const updateDataWithResponse = (name: string, data: any) => {
    q.value = data.q;
    eigenvalues.value = data.eigenvalues;
    theoreticalCurve.value = data.theoretical_curve;
    lambdaPlus.value = data.lambda_plus;
    lambdaMinus.value = data.lambda_minus;
    
    const dsIdx = uploadedDatasets.value.findIndex(d => d.name === name);
    const dsResult = {
        name, q: data.q, sigmaSq: sigmaSq.value, eigenvalues: data.eigenvalues,
        theoreticalCurve: data.theoretical_curve, lambdaPlus: data.lambda_plus,
        lambdaMinus: data.lambda_minus, sparsity: data.sparsity, n: data.n, p: data.p,
        outlier_eigenvectors: data.outlier_eigenvectors || [],
        column_names: data.column_names || [], ipr: data.ipr || [],
        cleaned_heatmap_base64: data.cleaned_heatmap_base64
    };
    if (dsIdx >= 0) uploadedDatasets.value[dsIdx] = dsResult;
    else uploadedDatasets.value.push(dsResult);
};

const triggerUpload = () => fileInput.value?.click();

const handleFileUpload = async (e: Event) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;
    loading.value = true;
    currentModel.value = 'MP';
    currentDataset.value = file.name;
    try {
        const textData = await file.text();
        const lines = textData.split('\n').filter(l => l.trim().length > 0);
        fileLinesCache.value = lines;
        maxRows.value = lines.length;
        rowRange.value = [0, maxRows.value];
        
        const data = await uploadMatrix(file, Math.sqrt(sigmaSq.value), fillStrategy.value, useStandardization.value);
        updateDataWithResponse(file.name, data);
        
        // Cache original lines for slider window slicing
        const ds = uploadedDatasets.value.find(d => d.name === file.name);
        if (ds) ds.originalLines = lines;

    } catch (err: any) { alert("Upload Error: " + err.message); }
    finally { 
        loading.value = false; 
        if (fileInput.value) fileInput.value.value = '';
    }
};

const fetchData = async () => {
    loading.value = true;
    currentDataset.value = '';
    try {
        if (currentModel.value === 'MP') {
            const p = 350;
            const n = Math.floor(p / q.value);
            const data = await fetchMPData(n, p, Math.sqrt(sigmaSq.value));
            eigenvalues.value = data.eigenvalues;
            theoreticalCurve.value = data.theoretical_curve;
            lambdaPlus.value = data.lambda_plus;
            lambdaMinus.value = data.lambda_minus;
        } else {
            const data = await fetchWignerData(1000, Math.sqrt(sigmaSq.value));
            eigenvalues.value = data.eigenvalues;
            theoreticalCurve.value = data.theoretical_curve;
            const r = 2 * Math.sqrt(sigmaSq.value) * Math.sqrt(1000);
            lambdaPlus.value = r; lambdaMinus.value = -r;
        }
    } finally { loading.value = false; }
};

const debouncedFetch = () => { fetchData(); };
const switchModel = (m: 'MP' | 'WIGNER') => { currentModel.value = m; fetchData(); };
const handleAnomalies = (l: number[]) => { anomalies.value = l; };
const handleOutlierClick = (idx: number) => {
    expandedEigenvector.value = idx;
    nextTick(() => {
        document.getElementById(`anomaly-${idx}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
};

const toggleEigenvectorDetail = (i: number) => expandedEigenvector.value = expandedEigenvector.value === i ? null : i;
const getEigenvectorForAnomaly = (idx: number) => {
    const ds = uploadedDatasets.value.find(d => d.name === currentDataset.value);
    return ds?.outlier_eigenvectors?.find((oe: any) => oe.rank === idx + 1) || null;
};
const getMaxWeight = (idx: number) => {
    const oe = getEigenvectorForAnomaly(idx);
    return oe ? Math.max(...oe.top_components.map((c: any) => c.abs_weight), 0.001) : 1;
};
const columnNames = computed(() => uploadedDatasets.value.find(d => d.name === currentDataset.value)?.column_names || []);

const selectDataset = (n: string) => {
    currentDataset.value = n;
    if (!n) fetchData();
    else {
        const ds = uploadedDatasets.value.find(d => d.name === n);
        if (ds) {
            eigenvalues.value = ds.eigenvalues;
            theoreticalCurve.value = ds.theoreticalCurve;
            lambdaPlus.value = ds.lambdaPlus;
            lambdaMinus.value = ds.lambdaMinus;
            q.value = ds.q;
        }
    }
    closeDropdown();
};
const toggleDropdown = () => isDropdownOpen.value = !isDropdownOpen.value;
const closeDropdown = () => isDropdownOpen.value = false;
const deleteDataset = (n: string, e: Event) => {
    e.stopPropagation();
    uploadedDatasets.value = uploadedDatasets.value.filter(d => d.name !== n);
    if (currentDataset.value === n) selectDataset('');
};

const dsHasFileConfigured = () => !!uploadedDatasets.value.find(d => d.name === currentDataset.value)?.originalLines;
const formatTooltip = (v: number) => v.toString();
const handleSliderChange = () => {}; // Re-processing can be added back if needed
const reprocessFile = () => {};

const openAiDrawer = () => isAiDrawerOpen.value = true;
const generateReport = async () => {
    if (!currentDataset.value) return;
    const ds = uploadedDatasets.value.find(d => d.name === currentDataset.value);
    isGenerating.value = true;
    aiReport.value = '';
    try {
        await streamAnalyze({
            dataset_name: ds.name, n: ds.n, p: ds.p, q: ds.q, sparsity: ds.sparsity,
            lambda_plus: ds.lambdaPlus, lambda_minus: ds.lambdaMinus,
            top_eigenvalues: ds.eigenvalues.slice(0, 5), outlier_count: ds.outlier_eigenvectors.length,
            model_name: aiSettings.value.modelName, api_key: aiSettings.value.apiKey, base_url: aiSettings.value.baseUrl
        }, (c) => aiReport.value += c);
    } finally { isGenerating.value = false; }
};
const renderedMarkdown = computed(() => marked.parse(aiReport.value || '点击下方生成报告...'));

onMounted(() => {
    loadExampleList();
    fetchData();
});
</script>

<style>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

.eigvec-slide-enter-active, .eigvec-slide-leave-active { transition: all 0.3s ease; max-height: 500px; overflow: hidden; }
.eigvec-slide-enter-from, .eigvec-slide-leave-to { opacity: 0; max-height: 0; }
</style>
