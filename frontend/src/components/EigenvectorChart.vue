<template>
  <div ref="chartRef" class="w-full min-h-[250px]"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue';
import * as echarts from 'echarts';

interface Props {
  eigenvector: any;
  columnNames: string[];
  lang?: 'zh' | 'en';
}
const props = defineProps<Props>();

const chartRef = ref<HTMLElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

const renderChart = () => {
  if (!chartInstance || !props.eigenvector || !props.eigenvector.vector) return;

  const vector = props.eigenvector.vector as number[];
  const labels = vector.map((_, i) => 
    (props.columnNames && props.columnNames.length > i) ? props.columnNames[i] : `Var ${i+1}`
  );

  const barData = vector.map((val, i) => {
    return {
      value: val,
      itemStyle: {
        color: val >= 0 
          ? new echarts.graphic.LinearGradient(0, 0, 0, 1, [{offset: 0, color: '#34d399'}, {offset: 1, color: '#059669'}]) // Emerald
          : new echarts.graphic.LinearGradient(0, 1, 0, 0, [{offset: 0, color: '#fb7185'}, {offset: 1, color: '#e11d48'}]) // Rose
      }
    };
  });

  const option = {
    backgroundColor: 'transparent',
    tooltip: { 
      trigger: 'axis', 
      backgroundColor: 'rgba(25, 25, 35, 0.9)', 
      borderColor: 'rgba(255,255,255,0.2)', 
      textStyle: { color: '#fff' },
      formatter: (params: any) => {
        const p = params[0];
        const val = p.value as number;
        const signStr = val >= 0 ? '+' : '';
        const color = val >= 0 ? '#34d399' : '#fb7185';
        return `
          <div style="font-size: 12px; color: rgba(255,255,255,0.7); margin-bottom: 4px;">${p.name}</div>
          <div style="font-family: monospace; font-weight: bold; color: ${color};">
            Weight: ${signStr}${val.toFixed(4)}
          </div>
        `;
      }
    },
    grid: { left: '3%', right: '3%', bottom: '15%', top: '15%', containLabel: true },
    dataZoom: [
      {
        type: 'slider',
        show: true,
        start: 0,
        end: Math.min((50 / vector.length) * 100, 100), // Show ~50 bars max initially
        textStyle: { color: 'rgba(255,255,255,0.5)' },
        borderColor: 'rgba(255,255,255,0.1)',
        fillerColor: 'rgba(10, 132, 255, 0.2)',
        handleStyle: { color: '#0A84FF' },
        bottom: '2%',
        height: 12
      },
      {
        type: 'inside',
        start: 0,
        end: 100,
        zoomOnMouseWheel: true,
        moveOnMouseMove: true
      }
    ],
    xAxis: { 
      type: 'category', 
      data: labels,
      axisLabel: { 
        color: 'rgba(255,255,255,0.6)', 
        fontSize: 10,
        interval: 'auto',
        hideOverlap: true
      },
      axisTick: { show: false },
      splitLine: { show: false }
    },
    yAxis: { 
      type: 'value', 
      name: props.lang === 'zh' ? '特征向量权重 (Loadings)' : 'Eigenvector Loadings',
      nameTextStyle: { color: 'rgba(255,255,255,0.5)' },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }, 
      axisLabel: { color: 'rgba(255,255,255,0.6)', fontFamily: 'monospace', fontSize: 10 }
    },
    series: [
      {
        name: 'Weight', 
        type: 'bar', 
        data: barData,
        barMaxWidth: 30,
        markLine: {
          symbol: ['none', 'none'],
          silent: true,
          label: { show: false },
          lineStyle: { type: 'solid', color: 'rgba(255,255,255,0.2)', width: 1 },
          data: [{ yAxis: 0 }]
        }
      }
    ]
  };
  
  chartInstance.setOption(option as echarts.EChartsOption, true);
};

onMounted(() => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value);
    renderChart();
    window.addEventListener('resize', handleResize);
  }
});

onUnmounted(() => {
  if (chartInstance) {
    window.removeEventListener('resize', handleResize);
    chartInstance.dispose();
  }
});

const handleResize = () => chartInstance?.resize();

watch(() => [props.eigenvector, props.lang], () => {
  renderChart();
}, { deep: true });

</script>
