<template>
  <div ref="chartRef" class="w-full flex-1 min-h-[300px] mt-12 transition-all duration-300"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue';
import * as echarts from 'echarts';

interface Props {
  model: 'MP' | 'WIGNER';
  eigenvalues: number[];
  theoreticalCurve: { x: number[], y: number[] } | null;
  bins: number;
  lambdaPlus: number;
  lambdaMinus: number;
  normType?: 'density' | 'count';
  lang?: 'zh' | 'en';
  highlightAnomalyIndex?: number | null;
}
const props = defineProps<Props>();
const emit = defineEmits(['anomalies', 'outlier-click']);

const chartRef = ref<HTMLElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

// Track which bar indices are outliers for click-to-panel interaction
let outlierBarIndices: number[] = [];

function createHistogram(data: number[], binsCount: number) {
  if(data.length === 0) return { hist: [] };
  const min = Math.min(...data);
  const max = Math.max(...data);
  
  // Automatically size bins emphasizing the bulk region, avoiding extreme outlier squashing
  let coreMax = max;
  if (props.model === 'MP' && props.lambdaPlus > 0 && max > props.lambdaPlus * 2) {
      coreMax = props.lambdaPlus * 1.2;
  } else if (props.model === 'WIGNER' && props.lambdaPlus > 0 && max > props.lambdaPlus * 2) {
      coreMax = props.lambdaPlus * 1.2;
  }
  const binWidth = Math.max((coreMax - min) / binsCount, 0.00001);
  const maxIdx = Math.min(Math.floor((max - min) / binWidth), 5000); 
  
  const counts = new Float32Array(maxIdx + 1);
  data.forEach(val => {
      let idx = Math.floor((val - min) / binWidth);
      if (idx > maxIdx) idx = maxIdx; // Safely pool massive extrema into the upper lip 
      if (idx >= 0) counts[idx]++;
  });

  const hist = [];
  for (let i = 0; i <= maxIdx; i++) {
      if (counts[i] > 0 || i <= binsCount * 1.5) { 
          const binCenter = min + (i + 0.5) * binWidth;
          const density = props.normType === 'count' ? counts[i] : ((counts[i] / data.length) / binWidth);
          hist.push([binCenter, density]);
      }
  }
  return { hist };
}

const renderChart = () => {
  if (!chartInstance) return;

  const lineData = props.theoreticalCurve?.x.map((val, i) => [val, props.theoreticalCurve!.y[i]]) || [];
  
  let barData: any[] = [];
  let anomalies: number[] = [];
  outlierBarIndices = [];
  
  if (props.eigenvalues.length > 0) {
    const histData = createHistogram(props.eigenvalues, props.bins);
    barData = histData.hist.map((item, idx) => {
      const isOutlier = item[0] > props.lambdaPlus || (props.model === 'WIGNER' && item[0] < props.lambdaMinus);
      if (isOutlier) outlierBarIndices.push(idx);
      return {
        value: item,
        itemStyle: {
          color: isOutlier 
            ? new echarts.graphic.LinearGradient(0, 0, 0, 1, [{offset: 0, color: '#FF9F0A'}, {offset: 1, color: '#FF453A'}])
            : new echarts.graphic.LinearGradient(0, 0, 0, 1, [{offset: 0, color: '#5AC8FA'}, {offset: 1, color: '#0A84FF'}]),
          borderRadius: [4, 4, 0, 0]
        }
      };
    });
    
    anomalies = props.eigenvalues.filter(x => x > props.lambdaPlus || (props.model === 'WIGNER' && x < props.lambdaMinus)).sort((a,b)=>b-a);
    emit('anomalies', anomalies);
  }

  let zoomEnd = 100;
  if (props.eigenvalues.length > 0 && props.lambdaPlus > 0) {
      const maxVal = Math.max(...props.eigenvalues);
      if (maxVal > props.lambdaPlus * 2) {
          zoomEnd = Math.min(((props.lambdaPlus * 1.5) / maxVal) * 100, 100);
          zoomEnd = Math.max(zoomEnd, 1); 
      }
  }

  const markLineData = props.model === 'MP' ? [{ xAxis: props.lambdaPlus }] : [{ xAxis: props.lambdaPlus }, { xAxis: props.lambdaMinus }];

  const option = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(25, 25, 35, 0.9)', borderColor: 'rgba(255,255,255,0.2)', textStyle: { color: '#fff' } },
    grid: { left: '5%', right: '8%', bottom: '15%', top: '15%', containLabel: true },
    dataZoom: [
      {
        type: 'slider',
        show: true,
        xAxisIndex: [0],
        start: 0,
        end: zoomEnd,
        textStyle: { color: 'rgba(255,255,255,0.5)' },
        borderColor: 'rgba(255,255,255,0.1)',
        fillerColor: 'rgba(10, 132, 255, 0.2)',
        handleStyle: { color: '#0A84FF' },
        bottom: '2%'
      },
      {
        type: 'inside',
        xAxisIndex: [0],
        start: 0,
        end: zoomEnd,
        zoomOnMouseWheel: true,
        moveOnMouseMove: true
      }
    ],
    xAxis: { type: 'value', name: props.lang === 'zh' ? '特征值 (λ)' : 'Eigenvalue (λ)', nameTextStyle: { color: 'rgba(255,255,255,0.5)', padding: [0, 0, -30, 0] }, splitLine: { show: false }, axisLabel: { color: 'rgba(255,255,255,0.6)', fontFamily: 'monospace' } },
    yAxis: { type: 'value', name: props.normType === 'count' ? (props.lang === 'zh' ? '频数 (Count)' : 'Count') : (props.lang === 'zh' ? '概率密度 ρ(λ)' : 'Density ρ(λ)'), splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }, axisLabel: { color: 'rgba(255,255,255,0.6)' } },
    series: [
      {
        name: props.lang === 'zh' ? '经验特征值分布' : 'Empirical Eigenvalues', type: 'bar', barWidth: '95%',
        data: barData
      },
      {
        name: props.lang === 'zh' ? '理论分布曲线' : 'Theoretical Curve', type: 'line', smooth: true, symbol: 'none', data: lineData,
        lineStyle: { color: '#32D74B', width: 3, shadowBlur: 10, shadowColor: 'rgba(50, 215, 75, 0.5)' },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(50, 215, 75, 0.3)' }, { offset: 1, color: 'rgba(50, 215, 75, 0.0)' }]) },
        markLine: {
          symbol: ['none', 'none'],
          label: { show: true, position: 'middle', formatter: props.lang === 'zh' ? '理论边界' : 'Theory Bound', color: '#FF453A' },
          lineStyle: { type: 'dashed', color: '#FF453A', width: 2 },
          data: markLineData
        }
      }
    ]
  };
  chartInstance.setOption(option as echarts.EChartsOption, true);
  
  // Apply highlight if an anomaly is selected from the panel
  applyHighlight();
};

// Highlight outlier bars when panel selection changes
const applyHighlight = () => {
  if (!chartInstance || outlierBarIndices.length === 0) return;
  
  // First, reset all bars to default
  chartInstance.dispatchAction({ type: 'downplay', seriesIndex: 0 });
  
  if (props.highlightAnomalyIndex !== null && props.highlightAnomalyIndex !== undefined) {
    // Highlight all outlier bars with a glowing effect by re-setting their itemStyle
    outlierBarIndices.forEach(barIdx => {
      chartInstance!.dispatchAction({
        type: 'highlight',
        seriesIndex: 0,
        dataIndex: barIdx
      });
    });
  }
};

onMounted(() => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value);
    renderChart();
    window.addEventListener('resize', handleResize);
    
    // Chart → Panel: click anywhere in grid to select closest outlier
    chartInstance.getZr().on('click', (params: any) => {
      if (!chartInstance || props.eigenvalues.length === 0) return;
      const pointInPixel = [params.offsetX, params.offsetY];
      if (chartInstance.containPixel('grid', pointInPixel)) {
        const xValue = chartInstance.convertFromPixel({ seriesIndex: 0 }, pointInPixel)[0];
        
        // Find if clicked in outlier region
        if (xValue > props.lambdaPlus || (props.model === 'WIGNER' && xValue < props.lambdaMinus)) {
            const anomalies = props.eigenvalues.filter(x => x > props.lambdaPlus || (props.model === 'WIGNER' && x < props.lambdaMinus)).sort((a,b)=>b-a);
            
            if (anomalies.length > 0) {
                let closestIdx = 0;
                let minDiff = Math.abs(anomalies[0] - xValue);
                for(let i = 1; i < anomalies.length; i++) {
                    const diff = Math.abs(anomalies[i] - xValue);
                    if (diff < minDiff) {
                        minDiff = diff;
                        closestIdx = i;
                    }
                }
                emit('outlier-click', closestIdx);
            }
        }
      }
    });
  }
});

onUnmounted(() => {
  if (chartInstance) {
    window.removeEventListener('resize', handleResize);
    chartInstance.dispose();
  }
});

const handleResize = () => chartInstance?.resize();

const exportChart = () => {
  if (chartInstance) {
    const dataUrl = chartInstance.getDataURL({ type: 'png', backgroundColor: '#0f0c29', pixelRatio: 2 });
    const link = document.createElement('a');
    link.download = props.lang === 'zh' ? `RMT_分析_${props.model}.png` : `RMT_Analysis_${props.model}.png`;
    link.href = dataUrl;
    link.click();
  }
};
defineExpose({ exportChart });

watch(() => [props.eigenvalues, props.theoreticalCurve, props.bins, props.model, props.normType, props.lang], () => {
  renderChart();
}, { deep: true });

// Watch for highlight changes from panel interaction
watch(() => props.highlightAnomalyIndex, () => {
  applyHighlight();
});

</script>
