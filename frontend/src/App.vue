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
    <nav class="w-full px-8 py-6 flex justify-between items-center z-10">
        <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-gradient-to-tr from-iosBlue to-purple-500 flex items-center justify-center font-bold">R</div>
            <span class="text-xl font-semibold tracking-tight text-white/90">
                {{ lang === 'zh' ? '随机矩阵分析' : 'RMT Analytics' }}
            </span>
        </div>
        <div class="flex items-center gap-4">
            <!-- Language Toggle -->
            <div class="flex items-center gap-1 bg-black/30 rounded-full p-1 border border-white/10">
                <button @click="lang = 'zh'" :class="lang === 'zh' ? 'bg-white/20 text-white shadow rounded-full px-3 py-1 text-xs transition' : 'text-white/50 hover:text-white px-3 py-1 text-xs transition'">中</button>
                <button @click="lang = 'en'" :class="lang === 'en' ? 'bg-white/20 text-white shadow rounded-full px-3 py-1 text-xs transition' : 'text-white/50 hover:text-white px-3 py-1 text-xs transition'">EN</button>
            </div>
            
            <button @click="rmtChartRef?.exportChart()" class="glass-panel px-6 py-2 text-sm font-medium hover:bg-white/10 transition duration-300 flex items-center gap-2">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                {{ lang === 'zh' ? '导出图表' : 'Export Chart' }}
            </button>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="flex-grow px-4 lg:px-8 pb-8 lg:pb-12 grid grid-cols-1 lg:grid-cols-12 gap-6 z-10 w-full 3xl:max-w-[2000px] 3xl:mx-auto">
        
        <!-- Left Column: Controls & Upload -->
        <div class="lg:col-span-4 xl:col-span-3 flex flex-col gap-6">
            
            <!-- Real Upload Area (Trigger File Input) -->
            <div @click="triggerUpload" class="glass-panel p-6 flex flex-col items-center justify-center text-center cursor-pointer hover:bg-white/10 transition group border-dashed border-2 border-white/20 relative">
                <input type="file" ref="fileInput" accept=".csv" class="hidden" @click.stop @change="handleFileUpload">
                <svg class="w-12 h-12 text-white/60 mb-4 group-hover:text-iosBlue transition" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
                <h3 class="font-medium text-lg text-white">{{ lang === 'zh' ? '上传真实矩阵数据' : 'Upload Real Matrix' }}</h3>
                <p class="text-white/50 text-xs mt-2">{{ lang === 'zh' ? 'CSV 格式 (列=特征)' : 'CSV Format (Columns=Features)' }}</p>
            </div>

            <!-- Model Switcher -->
            <div class="glass-panel p-2 flex bg-black/20 rounded-full mx-2">
                <button @click="switchModel('MP')" :class="currentModel === 'MP' ? 'flex-1 py-2 text-sm font-medium rounded-full bg-white/20 shadow text-white transition' : 'flex-1 py-2 text-sm font-medium rounded-full text-white/60 hover:text-white transition'">{{ lang === 'zh' ? 'Marchenko-Pastur 分布' : 'Marchenko-Pastur' }}</button>
                <button @click="switchModel('WIGNER')" :class="currentModel === 'WIGNER' ? 'flex-1 py-2 text-sm font-medium rounded-full bg-white/20 shadow text-white transition' : 'flex-1 py-2 text-sm font-medium rounded-full text-white/60 hover:text-white transition'">{{ lang === 'zh' ? 'Wigner 半圆律' : 'Wigner Semicircle' }}</button>
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
                        <!-- Expanded Eigenvector Detail Panel with slide animation -->
                        <Transition name="eigvec-slide">
                        <div v-if="expandedEigenvector === index && getEigenvectorForAnomaly(index)" class="px-3 pb-3 pt-1 border-t border-white/10 bg-black/20">
                            <p class="text-[10px] text-white/40 mb-2 uppercase tracking-wider">{{ lang === 'zh' ? '特征向量成分权重 (Top-5)' : 'Eigenvector Component Weights (Top-5)' }}</p>
                            <div class="space-y-1.5">
                                <div v-for="(comp, ci) in getEigenvectorForAnomaly(index).top_components" :key="ci" 
                                     class="flex items-center gap-2 eigvec-bar-enter"
                                     :style="{ animationDelay: (ci * 80) + 'ms' }">
                                    <!-- Column name -->
                                    <span class="text-[11px] text-white/70 w-[90px] truncate shrink-0" :title="comp.column_name">{{ comp.column_name }}</span>
                                    <!-- Visual bar with animated fill -->
                                    <div class="flex-1 h-4 bg-black/30 rounded-sm relative overflow-hidden">
                                        <div class="absolute top-0 left-0 h-full rounded-sm eigvec-bar-fill"
                                             :class="comp.weight >= 0 ? 'bg-gradient-to-r from-emerald-500/80 to-emerald-400/60' : 'bg-gradient-to-r from-rose-500/80 to-rose-400/60'"
                                             :style="{ '--target-width': (comp.abs_weight / getMaxWeight(index) * 100) + '%', animationDelay: (ci * 80 + 100) + 'ms' }">
                                        </div>
                                        <span class="absolute inset-0 flex items-center justify-end pr-1 text-[9px] font-mono text-white/60">
                                            {{ comp.weight >= 0 ? '+' : '' }}{{ comp.weight.toFixed(3) }}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <div class="mt-2 flex gap-3 text-[9px] text-white/30">
                                <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-sm bg-emerald-500/80"></span>{{ lang === 'zh' ? '正相关' : 'Positive' }}</span>
                                <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-sm bg-rose-500/80"></span>{{ lang === 'zh' ? '负相关 (对抗)' : 'Negative (opposing)' }}</span>
                            </div>
                        </div>
                        </Transition>
                        <!-- No eigenvector data message -->
                        <Transition name="eigvec-slide">
                        <div v-if="expandedEigenvector === index && !getEigenvectorForAnomaly(index)" class="px-3 pb-3 pt-1 border-t border-white/10 bg-black/20">
                            <p class="text-[10px] text-white/30 italic">{{ lang === 'zh' ? '未提取特征向量（仅上传数据集时可用）' : 'No eigenvector data (available for uploaded datasets only)' }}</p>
                        </div>
                        </Transition>
                    </div>
                </div>
            </div>

        </div>

        <!-- Right Column: Visualization -->
        <div class="lg:col-span-8 xl:col-span-9 glass-panel p-2 flex flex-col relative overflow-hidden min-h-[600px] lg:h-[calc(100vh-140px)] lg:sticky lg:top-8">
            <div class="absolute top-4 left-6 z-10 pointer-events-none flex flex-col gap-2">
                <div class="flex items-center pointer-events-auto">
                    <h2 class="text-2xl font-bold tracking-tight">
                        {{ currentModel === 'MP' ? (lang === 'zh' ? 'Marchenko-Pastur 谱分布' : 'Marchenko-Pastur Spectrum') : (lang === 'zh' ? 'Wigner 半圆律谱分布' : 'Wigner Semicircle Spectrum') }}
                    </h2>
                    <!-- Custom Apple-style Dropdown -->
                    <div v-if="uploadedDatasets.length > 0" class="ml-4 relative flex items-center">
                        <button @click="toggleDropdown" 
                                class="flex items-center justify-between px-4 py-1.5 bg-black/30 backdrop-blur-xl hover:bg-white/10 text-white/90 text-sm rounded-full border border-white/10 font-medium tracking-tight focus:outline-none focus:ring-1 focus:ring-iosBlue/50 cursor-pointer transition-all shadow-sm w-[240px]"
                                :title="lang === 'zh' ? '选择数据集' : 'Select Dataset'">
                            <span class="truncate">{{ currentDataset || (lang === 'zh' ? '模拟生成中心...' : 'Simulation Hub...') }}</span>
                            <svg class="w-3 h-3 ml-2 text-white/50 shrink-0 transition-transform duration-200" :class="{'rotate-180': isDropdownOpen}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                        </button>

                        <!-- Invisible Overlay for closing -->
                        <div v-if="isDropdownOpen" @click="closeDropdown" class="fixed inset-0 z-40"></div>

                        <!-- Dropdown Menu Container -->
                        <div v-if="isDropdownOpen" 
                             class="absolute top-10 left-0 w-[240px] z-50 bg-[#1c1c1e]/90 backdrop-blur-3xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col p-1.5">
                            
                            <div class="max-h-[240px] overflow-y-auto pr-1" style="scrollbar-width: thin; scrollbar-color: rgba(255,255,255,0.2) transparent;">
                                <!-- Simulation Hub Option -->
                                <div @click="selectDataset('')" 
                                     class="px-3 py-2 text-sm text-white/60 hover:bg-white/10 rounded-xl cursor-pointer transition-colors flex items-center gap-2 mb-1">
                                     <div class="w-2 h-2 rounded-full" :class="!currentDataset ? 'bg-iosBlue' : 'bg-transparent border border-white/30'"></div>
                                     {{ lang === 'zh' ? '模拟生成中心...' : 'Simulation Hub...' }}
                                </div>
                                
                                <div class="h-px bg-white/10 mx-2 mb-1"></div>

                                <!-- Uploaded Datasets -->
                                <div v-for="ds in uploadedDatasets" :key="ds.name" 
                                     @click="selectDataset(ds.name)"
                                     class="px-3 py-2 text-sm text-white/90 hover:bg-white/10 rounded-xl cursor-pointer transition-colors flex flex-col gap-0.5 group relative">
                                    <div class="flex items-center justify-between">
                                        <div class="flex items-center gap-2 overflow-hidden pr-2">
                                            <div class="w-2 h-2 rounded-full shrink-0" :class="currentDataset === ds.name ? 'bg-iosGreen' : 'bg-transparent border border-white/30'"></div>
                                            <span class="font-medium truncate">{{ ds.name }}</span>
                                        </div>
                                        <button @click="(e) => deleteDataset(ds.name, e)" class="opacity-0 group-hover:opacity-100 absolute right-2 p-1 hover:bg-white/20 rounded text-white/40 hover:text-iosRed transition-all" :title="lang === 'zh' ? '删除数据集' : 'Remove dataset'">
                                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                                        </button>
                                    </div>
                                    <span class="text-xs text-white/40 font-mono ml-4">q={{ ds.q.toFixed(2) }} | {{ lang === 'zh' ? '稀疏度=' : 'sparsity=' }}{{ (ds.sparsity*100).toFixed(0) }}%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <p class="text-white/50 text-sm">{{ lang === 'zh' ? '经验特征值分布 vs. 理论概率密度' : 'Empirical Distribution vs. Theoretical Density' }}</p>
            </div>
            
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

            <!-- Eigenvector Full Chart (Slide up when expanded) -->
            <Transition name="eigvec-slide">
              <div v-if="expandedEigenvector !== null && getEigenvectorForAnomaly(expandedEigenvector)" class="w-full mt-2 border border-white/10 relative bg-black/30 backdrop-blur-md rounded-2xl overflow-hidden shadow-lg z-10 shrink-0 mb-2">
                <div class="px-4 py-2 flex justify-between items-center bg-white/5 border-b border-white/10">
                   <h3 class="text-sm font-bold text-white/80 font-mono">
                     {{ lang === 'zh' ? '完整特征向量 Loadings (λ=' + getEigenvectorForAnomaly(expandedEigenvector).eigenvalue.toFixed(4) + ')' : 'Full Eigenvector Loadings (λ=' + getEigenvectorForAnomaly(expandedEigenvector).eigenvalue.toFixed(4) + ')' }}
                   </h3>
                   <button @click="expandedEigenvector = null" class="text-white/40 hover:text-white transition p-1 rounded-full hover:bg-white/10">
                     <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                   </button>
                </div>
                <EigenvectorChart 
                  :eigenvector="getEigenvectorForAnomaly(expandedEigenvector)"
                  :columnNames="columnNames"
                  :lang="lang"
                />
              </div>
            </Transition>

            <!-- AI Button and Settings -->
            <div class="absolute top-4 right-4 flex gap-2 z-20">
                <button @click="isAiSettingsOpen = true" class="p-1.5 bg-black/30 backdrop-blur border border-white/10 rounded-full hover:bg-white/10 transition text-white/50 hover:text-white shadow-sm" :title="lang === 'zh' ? 'AI 提供商设置' : 'AI Provider Settings'">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                </button>
                <button @click="openAiDrawer" class="flex items-center gap-2 px-4 py-1.5 bg-gradient-to-r from-indigo-500/80 to-purple-600/80 hover:from-indigo-500 hover:to-purple-600 border border-purple-400/30 text-white rounded-full text-sm font-medium shadow-[0_0_15px_rgba(124,58,237,0.3)] transition-all">
                    <span>✨ {{ lang === 'zh' ? 'AI 深度分析' : 'AI Insights' }}</span>
                </button>
            </div>
        </div>

    </main>

    <!-- AI Settings Modal -->
    <div v-if="isAiSettingsOpen" class="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in-down">
        <div class="bg-[#1c1c1e] border border-white/10 p-6 rounded-2xl w-[400px] shadow-2xl transition-all">
            <h3 class="text-xl font-bold text-white mb-4">{{ lang === 'zh' ? 'AI 模型提供商设置' : 'AI Provider Settings' }}</h3>
            <div class="flex flex-col gap-4">
                <div>
                    <label class="text-white/70 text-sm mb-1 block">{{ lang === 'zh' ? '接口地址 (Base URL)' : 'Base URL' }}</label>
                    <input v-model="aiSettings.baseUrl" type="text" class="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white text-sm" placeholder="http://localhost:11434/v1">
                </div>
                <div>
                    <label class="text-white/70 text-sm mb-1 block">{{ lang === 'zh' ? 'API Key (如果需要)' : 'API Key (if required)' }}</label>
                    <input v-model="aiSettings.apiKey" type="password" class="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white text-sm" placeholder="sk-...">
                </div>
                <div>
                    <label class="text-white/70 text-sm mb-1 block">{{ lang === 'zh' ? '模型名称 (Model Name)' : 'Model Name' }}</label>
                    <input v-model="aiSettings.modelName" type="text" class="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white text-sm" placeholder="qwen-plus, deepseek-r1...">
                </div>
            </div>
            <div class="mt-6 flex justify-end gap-3">
                <button @click="isAiSettingsOpen = false" class="px-4 py-2 rounded-lg bg-iosBlue text-white hover:bg-blue-600 transition text-sm font-medium">{{ lang === 'zh' ? '保存并关闭' : 'Save & Close' }}</button>
            </div>
        </div>
    </div>

    <!-- AI Insights Drawer -->
    <div class="fixed top-0 right-0 bottom-0 w-[450px] bg-[#1c1c1e]/95 backdrop-blur-3xl border-l border-white/10 shadow-2xl z-50 transition-transform duration-300 transform flex flex-col"
         :class="isAiDrawerOpen ? 'translate-x-0' : 'translate-x-full'">
        <div class="p-5 border-b border-white/10 flex justify-between items-center bg-black/20">
            <h3 class="text-lg font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-indigo-400 flex items-center gap-2">
                {{ lang === 'zh' ? '✨ 深度 AI 智能分析' : '✨ Deep AI Analysis' }}
            </h3>
            <button @click="isAiDrawerOpen = false" class="text-white/50 hover:text-white p-1 rounded-full bg-white/5 hover:bg-white/10 transition">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
            </button>
        </div>
        
        <div class="flex-1 overflow-y-auto p-6 prose prose-invert prose-sm max-w-none custom-scrollbar" v-html="renderedMarkdown">
        </div>
        
        <div class="p-4 border-t border-white/10 bg-black/30">
            <button @click="generateReport" :disabled="isGenerating || !currentDataset" 
                    class="w-full py-3 rounded-xl font-medium transition-all shadow-lg flex justify-center items-center gap-2"
                    :class="(isGenerating || !currentDataset) ? 'bg-white/10 text-white/30 cursor-not-allowed' : 'bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white'">
                <svg v-if="isGenerating" class="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span v-else>{{ lang === 'zh' ? '生成统计深度洞察' : 'Generate Statistical Insights' }}</span>
                <span v-if="isGenerating">{{ lang === 'zh' ? '正在分析特征值谱图...' : 'Analyzing Spectrum...' }}</span>
            </button>
            <p v-if="!currentDataset" class="text-center text-xs text-iosRed mt-2">{{ lang === 'zh' ? '需要选择一个经验数据集进行分析。' : 'Requires active empirical dataset.' }}</p>
        </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue';
import { marked } from 'marked';
// @ts-ignore
import markedKatex from 'marked-katex-extension';
import 'katex/dist/katex.min.css';
import RmtChart from './components/RmtChart.vue';
import EigenvectorChart from './components/EigenvectorChart.vue';
import { fetchWignerData, fetchMPData, uploadMatrix, streamAnalyze } from './api/rmt';

marked.use(markedKatex({ throwOnError: false, nonStandard: true }));

const fileInput = ref<HTMLInputElement | null>(null);
const rmtChartRef = ref<any>(null);
const lang = ref<'zh' | 'en'>('zh');
const fillStrategy = ref('zero');
const normType = ref<'density' | 'count'>('density');
const currentDataset = ref<string>('');
const useStandardization = ref(true);
const selectedDomain = ref('general');
const expandedEigenvector = ref<number | null>(null);

// Slider selection state
const maxRows = ref<number>(100);
const rowRange = ref<[number, number]>([0, 100]);
const fileLinesCache = ref<string[]>([]);
const isTimeScaleActive = ref<boolean>(false);

// Eigenvector panel helpers
const toggleEigenvectorDetail = (index: number) => {
    expandedEigenvector.value = expandedEigenvector.value === index ? null : index;
};

const getEigenvectorForAnomaly = (anomalyIndex: number) => {
    if (!currentDataset.value) return null;
    const ds = uploadedDatasets.value.find(d => d.name === currentDataset.value);
    if (!ds || !ds.outlier_eigenvectors || ds.outlier_eigenvectors.length === 0) return null;
    // anomalyIndex corresponds to sorted outliers (rank starts at 1)
    const rank = anomalyIndex + 1;
    return ds.outlier_eigenvectors.find((oe: any) => oe.rank === rank) || null;
};

const columnNames = computed(() => {
    if (!currentDataset.value) return [];
    const ds = uploadedDatasets.value.find(d => d.name === currentDataset.value);
    return ds?.column_names || [];
});

const getMaxWeight = (anomalyIndex: number) => {
    const oe = getEigenvectorForAnomaly(anomalyIndex);
    if (!oe || !oe.top_components || oe.top_components.length === 0) return 1;
    return Math.max(...oe.top_components.map((c: any) => c.abs_weight), 0.001);
};

const formatTooltip = (val: number) => {
    if (fileLinesCache.value.length === 0) return val.toString();
    let idx = Math.min(val, fileLinesCache.value.length - 1);
    
    // If it's index 0 and it's a header row, peek at index 1 for the actual start date
    if (idx === 0 && fileLinesCache.value[0].toLowerCase().startsWith('date')) {
        idx = Math.min(1, fileLinesCache.value.length - 1);
    }
    
    const line = fileLinesCache.value[idx];
    if (!line) return val.toString();
    
    // Attempt to parse the first column as the Date
    const firstCol = line.split(',')[0];
    return firstCol ? firstCol : val.toString();
};

interface DatasetResult {
    name: string;
    originalFile?: File;
    originalLines?: string[];
    hasTimeScale?: boolean;
    q: number;
    sigmaSq: number;
    eigenvalues: number[];
    theoreticalCurve: { x: number[], y: number[] } | null;
    lambdaPlus: number;
    lambdaMinus: number;
    sparsity: number;
    n: number;
    p: number;
    outlier_eigenvectors?: any[];
    column_names?: string[];
}
const uploadedDatasets = ref<DatasetResult[]>([]);

const isAiSettingsOpen = ref(false);
const isAiDrawerOpen = ref(false);
const isGenerating = ref(false);
const aiReport = ref('');
const aiSettings = ref({
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    apiKey: '',
    modelName: 'qwen-plus'
});

const renderedMarkdown = computed(() => {
    if (!aiReport.value) {
        return lang.value === 'zh' 
            ? '<div class="text-white/40 flex h-full items-center justify-center text-center italic mt-20">点击下方 [生成统计深度洞察] 以从特征值谱中提取数学与物理意义分析...</div>'
            : '<div class="text-white/40 flex h-full items-center justify-center text-center italic mt-20">Click [Generate Report] below to extract Mathematical Insights from the spectrum...</div>';
    }
    
    // Some AI models wrap the response in markdown code blocks, strip them out.
    let text = aiReport.value.trim();
    if (text.startsWith('```markdown')) {
        text = text.substring(11).trim();
    } else if (text.startsWith('```md')) {
        text = text.substring(5).trim();
    } else if (text.startsWith('```')) {
        text = text.substring(3).trim();
    }
    if (text.endsWith('```')) {
        text = text.slice(0, -3).trim();
    }
    
    return marked.parse(text);
});

const openAiDrawer = () => {
    isAiDrawerOpen.value = true;
};

const generateReport = async () => {
    if (!currentDataset.value) return;
    const ds = uploadedDatasets.value.find(d => d.name === currentDataset.value);
    if (!ds) return;
    
    const sorted = [...ds.eigenvalues].sort((a,b) => b-a);
    const topEqs = sorted.slice(0, 5);
    const outliers = sorted.filter(x => x > ds.lambdaPlus);
    
    // Protect undefined backward compatibles
    const n = ds.n || 1000;
    const p = ds.p || Math.floor(1000 * ds.q);

    // 构建特征向量成分摘要（供AI深度分析使用）
    let eigenvectorSummary = '';
    if (ds.outlier_eigenvectors && ds.outlier_eigenvectors.length > 0) {
        const lines: string[] = [];
        for (const oe of ds.outlier_eigenvectors) {
            lines.push(`\n▸ 异常特征值 #${oe.rank} (λ=${oe.eigenvalue.toFixed(4)})，其特征向量中权重最高的成分：`);
            for (const comp of oe.top_components) {
                const sign = comp.weight >= 0 ? '+' : '-';
                lines.push(`  - [${comp.column_name}] (列${comp.column_index}): 权重=${sign}${comp.abs_weight.toFixed(4)}`);
            }
        }
        eigenvectorSummary = lines.join('\n');
    }

    const params = {
        dataset_name: ds.name,
        n: n,
        p: p,
        q: ds.q,
        sparsity: ds.sparsity || 0,
        lambda_plus: ds.lambdaPlus,
        lambda_minus: ds.lambdaMinus,
        top_eigenvalues: topEqs,
        outlier_count: outliers.length,
        model_name: aiSettings.value.modelName,
        api_key: aiSettings.value.apiKey,
        base_url: aiSettings.value.baseUrl,
        eigenvector_summary: eigenvectorSummary
    };
    
    isGenerating.value = true;
    aiReport.value = '';
    
    try {
        await streamAnalyze(params, (chunkText) => {
            aiReport.value += chunkText;
        });
    } catch (e: any) {
        aiReport.value += `\n\n**Error:** ${e.message}`;
    } finally {
        isGenerating.value = false;
    }
}

const loadSavedDataset = () => {
    if (!currentDataset.value) return;
    const ds = uploadedDatasets.value.find(d => d.name === currentDataset.value);
    if (!ds) return;
    
    currentModel.value = 'MP';
    q.value = ds.q;
    sigmaSq.value = ds.sigmaSq;
    eigenvalues.value = ds.eigenvalues;
    theoreticalCurve.value = ds.theoreticalCurve;
    lambdaPlus.value = ds.lambdaPlus;
    lambdaMinus.value = ds.lambdaMinus;

    // Load lines cache and reset slider for loaded dataset
    if (ds.originalLines && ds.originalLines.length > 0) {
        fileLinesCache.value = ds.originalLines;
        maxRows.value = ds.originalLines.length;
        rowRange.value = [0, maxRows.value];
        isTimeScaleActive.value = !!ds.hasTimeScale;
    } else {
        fileLinesCache.value = [];
        isTimeScaleActive.value = false;
    }
};

const isDropdownOpen = ref(false);
const toggleDropdown = () => isDropdownOpen.value = !isDropdownOpen.value;
const closeDropdown = () => isDropdownOpen.value = false;

const selectDataset = (name: string) => {
    currentDataset.value = name;
    if (!name) {
        fetchData();
    } else {
        loadSavedDataset();
    }
    closeDropdown();
};

const deleteDataset = (name: string, e: Event) => {
    e.stopPropagation();
    uploadedDatasets.value = uploadedDatasets.value.filter(d => d.name !== name);
    if (currentDataset.value === name) {
        currentDataset.value = '';
        fetchData();
    }
};

const dsHasFileConfigured = () => {
    const ds = uploadedDatasets.value.find(d => d.name === currentDataset.value);
    return ds?.originalLines && ds.originalLines.length > 0;
};

const triggerUpload = () => {
    fileInput.value?.click();
}

const reprocessFile = async () => {
    if (!currentDataset.value || currentModel.value !== 'MP') return;
    const ds = uploadedDatasets.value.find(d => d.name === currentDataset.value);
    if (!ds || !ds.originalFile || !ds.originalLines) return;
    
    loading.value = true;
    try {
        const slicedLines = ds.originalLines.slice(rowRange.value[0], rowRange.value[1]);
        if (slicedLines.length === 0) {
            throw new Error("Selection is empty");
        }
        const fileBlob = new File([slicedLines.join('\n')], ds.name, { type: 'text/csv' });

        const data = await uploadMatrix(fileBlob, Math.sqrt(sigmaSq.value), fillStrategy.value, useStandardization.value);
        q.value = data.q;
        eigenvalues.value = data.eigenvalues;
        theoreticalCurve.value = data.theoretical_curve;
        lambdaPlus.value = data.lambda_plus;
        lambdaMinus.value = data.lambda_minus;
        
        ds.q = data.q;
        ds.sigmaSq = sigmaSq.value;
        ds.eigenvalues = data.eigenvalues;
        ds.theoreticalCurve = data.theoretical_curve;
        ds.lambdaPlus = data.lambda_plus;
        ds.lambdaMinus = data.lambda_minus;
        ds.sparsity = data.sparsity;
        ds.n = data.n;
        ds.p = data.p;
        ds.outlier_eigenvectors = data.outlier_eigenvectors || [];
        ds.column_names = data.column_names || [];
    } catch (err: any) {
        console.error("Reprocess Error:", err);
        alert(lang.value === 'zh' ? "❌ 重新处理错误:\n" + err.message : "❌ Reprocess Error:\n" + err.message);
    } finally {
        loading.value = false;
    }
};

const handleSliderChange = () => {
    reprocessFile();
};

const handleFileUpload = async (e: Event) => {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (!file) return;
    
    loading.value = true;
    currentModel.value = 'MP';
    currentDataset.value = file.name;
    try {
        // Read lines for client side sliding window slicing
        const textData = await file.text();
        const lines = textData.split('\n').filter(l => l.trim().length > 0);
        fileLinesCache.value = lines;
        maxRows.value = lines.length;
        rowRange.value = [0, maxRows.value];
        
        // Detect if first column is Date/Time
        let timeScale = false;
        if (lines.length > 0) {
            const firstColHeader = lines[0].split(',')[0].toLowerCase();
            if (firstColHeader.includes('date') || firstColHeader.includes('time') || firstColHeader.includes('day') || firstColHeader.includes('month') || firstColHeader.includes('year')) {
                timeScale = true;
            } else if (lines.length > 1) {
                const firstVal = lines[1].split(',')[0];
                if (!isNaN(Date.parse(firstVal)) && isNaN(Number(firstVal))) {
                    timeScale = true;
                }
            }
        }
        isTimeScaleActive.value = timeScale;

        const fileBlob = new File([lines.slice(rowRange.value[0], rowRange.value[1]).join('\n')], file.name, { type: 'text/csv' });
        const data = await uploadMatrix(fileBlob, Math.sqrt(sigmaSq.value), fillStrategy.value, useStandardization.value);
        q.value = data.q;
        eigenvalues.value = data.eigenvalues;
        theoreticalCurve.value = data.theoretical_curve;
        lambdaPlus.value = data.lambda_plus;
        lambdaMinus.value = data.lambda_minus;
        
        // Cache the dataset globally
        const newDataset: DatasetResult = {
            name: file.name,
            originalFile: file,
            originalLines: lines,
            hasTimeScale: timeScale,
            q: data.q,
            sigmaSq: sigmaSq.value,
            eigenvalues: data.eigenvalues,
            theoreticalCurve: data.theoretical_curve,
            lambdaPlus: data.lambda_plus,
            lambdaMinus: data.lambda_minus,
            sparsity: data.sparsity,
            n: data.n,
            p: data.p,
            outlier_eigenvectors: data.outlier_eigenvectors || [],
            column_names: data.column_names || []
        };
        const existIdx = uploadedDatasets.value.findIndex(d => d.name === file.name);
        if (existIdx >= 0) {
            uploadedDatasets.value[existIdx] = newDataset;
        } else {
            uploadedDatasets.value.push(newDataset);
        }
        
        if (data.sparsity > 0.5) {
            alert(lang.value === 'zh' 
                ? `⚠️ 警告: 上传的矩阵存在高稀疏度 (${(data.sparsity*100).toFixed(1)}% 的零值)。这会导致大量 0 特征值映射到谱分布中。`
                : `⚠️ Warning: The uploaded matrix has high sparsity (${(data.sparsity*100).toFixed(1)}% zeros). This will result in many 0-eigenvalues mapping onto the spectrum.`);
        }
    } catch (err: any) {
        console.error("Upload Data Error: ", err);
        alert(lang.value === 'zh' ? "❌ 数据上传错误:\n" + err.message : "❌ Data Upload Error:\n" + err.message);
    } finally {
        loading.value = false;
        if (fileInput.value) fileInput.value.value = '';
    }
};

const currentModel = ref<'MP' | 'WIGNER'>('MP');
const q = ref(0.35);
const sigmaSq = ref(1.00);
const bins = ref(50);
const loading = ref(false);

const eigenvalues = ref<number[]>([]);
const theoreticalCurve = ref<{ x: number[], y: number[] } | null>(null);
const lambdaPlus = ref(0.0);
const lambdaMinus = ref(0.0);
const anomalies = ref<number[]>([]);

let debounceTimeout: any = null;
const debouncedFetch = () => {
    if (debounceTimeout) clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
        fetchData();
    }, 300);
};

const switchModel = (model: 'MP' | 'WIGNER') => {
    currentModel.value = model;
    fetchData();
};

const handleAnomalies = (list: number[]) => {
    anomalies.value = list;
};

// Chart → Panel: clicking an outlier bar toggles the corresponding eigenvector panel
const handleOutlierClick = (anomalyIndex: number) => {
    expandedEigenvector.value = anomalyIndex; // Force expand
    
    // Auto-scroll the left panel to the expanded item
    nextTick(() => {
        const el = document.getElementById(`anomaly-${anomalyIndex}`);
        if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });
};

const fetchData = async () => {
    loading.value = true;
    currentDataset.value = '';
    try {
        if (currentModel.value === 'MP') {
            const p = 350;
            const n = Math.floor(p / q.value);
            const scale = Math.sqrt(sigmaSq.value);
            const data = await fetchMPData(n, p, scale);
            eigenvalues.value = data.eigenvalues;
            theoreticalCurve.value = data.theoretical_curve;
            lambdaPlus.value = data.lambda_plus;
            lambdaMinus.value = data.lambda_minus;
        } else {
            const n = 1000;
            const scale = Math.sqrt(sigmaSq.value);
            const data = await fetchWignerData(n, scale);
            eigenvalues.value = data.eigenvalues;
            theoreticalCurve.value = data.theoretical_curve;
            
            // Wigner info
            const r = 2 * scale * Math.sqrt(n);
            lambdaPlus.value = r;
            lambdaMinus.value = -r;
        }
    } catch (e: any) {
        console.error("Fetch Data Error: ", e);
        alert(lang.value === 'zh' ? "❌ 获取数据错误:\n" + e.message : "❌ Fetch Data Error:\n" + e.message);
    } finally {
        loading.value = false;
    }
};

onMounted(() => {
    fetchData();
});
</script>
