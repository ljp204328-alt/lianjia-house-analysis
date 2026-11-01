<template>
  <div class="detail-screen">
    <TechBackground />
    <header class="detail-header">
      <div class="back-btn-group">
        <div class="back-btn" @click="goBack">← 返回</div>
        <div v-if="isCityMode" class="back-btn" @click="goToProvince">↑ 返回{{ provinceName }}</div>
      </div>
      <div class="title-box">
        <dv-decoration-8 class="title-decoration"/>
        <div class="title">城市详情数据分析 - {{ provinceName }}</div>
        <dv-decoration-8 :reverse="true" class="title-decoration" />
      </div>
      <div class="header-right">
        <span class="info-value">当前城市：{{ isCityMode ? currentCityName : provinceName }}</span>
      </div>
    </header>

    <div class="detail-content">
      <div class="left-column">
        <div class="chart-box">
          <dv-border-box-7 class="box">
            <div class="box-header">城市 TOP</div>
            <div class="chart-container" style="position:relative">
              <div ref="cityTopChart" style="width:100%;height:100%"></div>
              <div ref="cityTopTooltip" style="display:none;position:absolute;z-index:9999;pointer-events:none;background:rgba(10,25,41,0.95);border:1px solid #00d4ff;border-radius:4px;padding:8px 12px;color:#fff;font-size:12px;line-height:1.6;white-space:nowrap;"></div>
            </div>
          </dv-border-box-7>
        </div>
        <div class="chart-box">
          <dv-border-box-7 class="box">
            <div class="box-header">价格分布</div>
            <div class="chart-container" style="position:relative">
              <div ref="priceDistChart" style="width:100%;height:100%"></div>
              <div ref="priceDistTooltip" style="display:none;position:absolute;z-index:9999;pointer-events:none;background:rgba(10,25,41,0.95);border:1px solid #00d4ff;border-radius:4px;padding:8px 12px;color:#fff;font-size:12px;line-height:1.6;white-space:nowrap;"></div>
            </div>
          </dv-border-box-7>
        </div>
        <div class="chart-box">
          <dv-border-box-7 class="box">
            <div class="box-header">面积分布</div>
            <div class="chart-container" style="position:relative">
              <div ref="areaDistChart" style="width:100%;height:100%"></div>
              <div ref="areaDistTooltip" style="display:none;position:absolute;z-index:9999;pointer-events:none;background:rgba(10,25,41,0.95);border:1px solid #00d4ff;border-radius:4px;padding:8px 12px;color:#fff;font-size:12px;line-height:1.6;white-space:nowrap;"></div>
            </div>
          </dv-border-box-7>
        </div>
      </div>

      <div class="center-map">
        <dv-border-box-7 class="map-box">
          <div class="map-container">
            <div id="echarts" class="map-layer echarts-layer"></div>
            <div id="gaode" class="map-layer gaode-layer"></div>
          </div>
        </dv-border-box-7>
      </div>

      <div class="right-column">
        <div class="chart-box">
          <dv-border-box-7 class="box">
            <div class="box-header">租赁方式占比</div>
            <div class="chart-container" ref="rentTypeChart"></div>
          </dv-border-box-7>
        </div>
        <div class="chart-box">
          <dv-border-box-7 class="box">
            <div class="box-header">最高价 TOP5</div>
            <div class="chart-container" style="position:relative">
              <div ref="topPriceChart" style="width:100%;height:100%"></div>
              <div ref="topPriceTooltip" style="display:none;position:absolute;z-index:9999;pointer-events:none;background:rgba(10,25,41,0.95);border:1px solid #00d4ff;border-radius:4px;padding:8px 12px;color:#fff;font-size:12px;line-height:1.6;white-space:nowrap;"></div>
            </div>
          </dv-border-box-7>
        </div>
        <div class="chart-box">
          <dv-border-box-7 class="box">
            <div class="box-header">均价/均面积</div>
            <div class="chart-container" style="position:relative">
              <div ref="avgPriceChart" style="width:100%;height:100%"></div>
              <div ref="avgPriceTooltip" style="display:none;position:absolute;z-index:9999;pointer-events:none;background:rgba(10,25,41,0.95);border:1px solid #00d4ff;border-radius:4px;padding:8px 12px;color:#fff;font-size:12px;line-height:1.6;white-space:nowrap;"></div>
            </div>
          </dv-border-box-7>
        </div>
      </div>
    </div>

    <!-- 楼盘房源列表弹窗 -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>楼盘房源列表 - {{ currentCommunity }}</h3>
          <span class="close-btn" @click="closeModal">×</span>
        </div>
        <div class="modal-body">
          <div v-if="houseList.length === 0" class="no-data">暂无数据</div>
          <div v-for="(house, index) in houseList" :key="index" class="house-item">
            <div class="house-img">
              <img :src="house.cover_image" alt="房屋图片" @error="handleImageError">
            </div>
            <div class="house-info">
              <div class="house-title">{{ house.title }}</div>
              <div class="house-desc">
                {{ house.area }}m² | {{ house.floor_type }}/{{ house.total_floors }}层
              </div>
              <div class="house-price">{{ house.price }} 元/月</div>
              <div class="house-tags">
                <span v-for="(tag, i) in (house.tags || '').split(' ')" :key="i" class="tag">{{ tag }}</span>
              </div>
              <a :href="house.detail_url" target="_blank" class="view-link">查看链接</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>


<script>
import * as echarts from 'echarts';
import 'echarts-gl';
import TechBackground from '@/components/TechBackground.vue';
import request from '@/utils/request';

const provinceCodeMap = {
  '北京市': '110000', '天津市': '120000', '河北省': '130000', '山西省': '140000',
  '内蒙古自治区': '150000', '辽宁省': '210000', '吉林省': '220000', '黑龙江省': '230000',
  '上海市': '310000', '江苏省': '320000', '浙江省': '330000', '安徽省': '340000',
  '福建省': '350000', '江西省': '360000', '山东省': '370000', '河南省': '410000',
  '湖北省': '420000', '湖南省': '430000', '广东省': '440000', '广西壮族自治区': '450000',
  '海南省': '460000', '重庆市': '500000', '四川省': '510000', '贵州省': '520000',
  '云南省': '530000', '西藏自治区': '540000', '陕西省': '610000', '甘肃省': '620000',
  '青海省': '630000', '宁夏回族自治区': '640000', '新疆维吾尔自治区': '650000',
  '台湾省': '710000', '香港特别行政区': '810000', '澳门特别行政区': '820000'
};

export default {
  name: 'CityDetail',
  components: { TechBackground },
  data() {
    return {
      provinceName: '',
      currentCityName: '',
      currentDistrictName: '',
      mapChart: null,
      cityTopChart: null,
      priceDistChart: null,
      areaDistChart: null,
      rentTypeChart: null,
      topPriceChart: null,
      avgPriceChart: null,
      apiData: null,
      cityTopStartIndex: 0,
      cityTopTimer: null,
      cityTopIsHovering: false,
      priceDistTimer: null,
      priceDistStartIndex: 0,
      priceDistIsHovering: false,
      areaDistTimer: null,
      areaDistStartIndex: 0,
      areaDistIsHovering: false,
      topPriceTimer: null,
      topPriceStartIndex: 0,
      topPriceIsHovering: false,
      avgPriceTimer: null,
      avgPriceStartIndex: 0,
      avgPriceIsHovering: false,
      gaodeMap: null,
      markersLayer: null,
      currentLocation: '112.938882,28.228304',
      gaodeApiKey: 'ab74b634fea2a4fa829c9fe5e3ecb542',
      isCityMode: false,
      isCommunityView: false,
      showModal: false,
      currentCommunity: '',
      houseList: []

    }
  },
  created() {
    this.districtMarkers = []
    this.communityMarkers = []
  },
  mounted() {
    this.provinceName = this.$route.query.province || '未知省份';
    this.$nextTick(() => {
      this.fetchDataAndInitCharts();
    });
  },
  beforeUnmount() {
    this.disposeAllCharts();
    if (this.cityTopTimer) clearInterval(this.cityTopTimer);
    if (this.priceDistTimer) clearInterval(this.priceDistTimer);
    if (this.areaDistTimer) clearInterval(this.areaDistTimer);
    if (this.topPriceTimer) clearInterval(this.topPriceTimer);
    if (this.avgPriceTimer) clearInterval(this.avgPriceTimer);
    if (this.gaodeMap) {
      this.gaodeMap.destroy();
    }
  },
  methods: {
    goBack() {
      this.$router.go(-1);
    },
    goToProvince() {
      if (!this.isCityMode) return;

      const echartsDiv = document.getElementById('echarts');
      const gaodeDiv = document.getElementById('gaode');

      if (gaodeDiv) gaodeDiv.style.opacity = '0';
      if (echartsDiv) echartsDiv.style.opacity = '1';

      setTimeout(() => {
        this.isCityMode = false;
        if (gaodeDiv) gaodeDiv.style.zIndex = '0';
        if (echartsDiv) echartsDiv.style.zIndex = '1';

        if (this.gaodeMap) {
          this.gaodeMap.destroy();
          this.gaodeMap = null;
        }

        this.initProvinceMap();
      }, 800);
    },
    disposeAllCharts() {
      [this.mapChart, this.cityTopChart, this.priceDistChart, this.areaDistChart,
        this.rentTypeChart, this.topPriceChart, this.avgPriceChart].forEach(chart => {
        if (chart) chart.dispose();
      });
    },
    async fetchDataAndInitCharts() {
      try {
        const response = await request.get('/analysis/api/province-data/', {
          params: { province: this.provinceName }
        });
        this.apiData = response.data;
        this.initAllCharts();
      } catch (err) {
        console.error('数据加载失败:', err);
      }
    },
    initAllCharts() {
      if (!this.apiData) return;
      this.initProvinceMap();
      this.initCityTopChart();
      this.initPriceDistChart();
      this.initAreaDistChart();
      this.initRentTypeChart();
      this.initTopPriceChart();
      this.initAvgPriceChart();
    },

    initProvinceMap() {
      const dom = document.getElementById('echarts');
      if (!dom) return;

      dom.style.opacity = '1';
      dom.style.zIndex = '1';

      this.mapChart = echarts.init(dom);

      const provinceCode = provinceCodeMap[this.provinceName];
      if (!provinceCode) return;

      let url;
      if (this.provinceName === '台湾省') {
        url = 'https://geo.datav.aliyun.com/areas_v2/bound/710000_full.json';
      } else {
        url = `https://geo.datav.aliyun.com/areas_v2/bound/${provinceCode}_full.json`;
      }

      fetch(url)
        .then(res => res.json())
        .then(geoJson => {
          echarts.registerMap('province', geoJson);

          this.mapChart.setOption({
            tooltip: {
              show: true,
              trigger: 'item',
              backgroundColor: 'rgba(10, 25, 41, 0.95)',
              borderColor: '#00d4ff',
              borderWidth: 1,
              padding: [10, 14],
              textStyle: { color: '#fff', fontSize: 13 },
              formatter: params => {
                if (!params.name || params.seriesType !== 'map3D') return '';
                const mapName = params.name;

                const cleanMapName = mapName
                  .replace(/(白族|傣族|彝族|哈尼族|壮族|苗族|回族|瑶族|僳族|佤族|拉祜族|布朗族|景颇族|阿昌族|德昂族|侗族|土家族)(自治)?州/g, '')
                  .replace(/市/g, '')
                  .replace(/地区/g, '')
                  .trim();

                const data = this.apiData.districts.find(d => {
                  const cleanDataName = d.name
                    .replace(/市/g, '')
                    .replace(/州/g, '')
                    .trim();

                  return cleanMapName === cleanDataName ||
                         d.name === mapName ||
                         d.name === mapName.replace('市', '') ||
                         mapName.includes(d.name) ||
                         d.name.includes(cleanMapName);
                });
                let html = `
                  <div style="min-width: 150px;">
                    <div style="margin-bottom: 6px; display: flex; justify-content: space-between;">
                      <span style="color: rgba(255,255,255,0.6); font-size: 12px;">地区</span>
                      <span style="color: #00d4ff; font-weight: bold; font-size: 14px;">${mapName}</span>
                    </div>
                `;

                if (data) {
                  html += `
                    <div style="display: flex; justify-content: space-between;">
                      <span style="color: rgba(255,255,255,0.6); font-size: 12px;">租房个数</span>
                      <span style="color: #00ffff; font-weight: bold; font-size: 14px;">${data.count}个</span>
                    </div>
                  `;
                }
                html += '</div>';
                return html;
              }
            },
            series: [{
              type: 'map3D',
              map: 'province',
              roam: true,
              boxHeight: 8,
              itemStyle: {
                color: '#1a3c5e',
                borderWidth: 1,
                borderColor: '#00d4ff'
              },
              emphasis: {
                itemStyle: { color: '#11b4da' },
                label: {
                  show: true,
                  textStyle: { color: '#ffffff', fontSize: 14 }
                }
              },
              label: {
                show: true,
                formatter: '{b}',
                distance: 8,
                textStyle: { color: '#ffffff', fontSize: 12 }
              },
              shading: 'lambert',
              light: {
                main: { intensity: 1.2, shadow: false, alpha: 50, beta: 10 },
                ambient: { intensity: 0.6 }
              },
              viewControl: {
                distance: 100,
                alpha: 60,
                beta: 0,
                autoRotate: false
              }
            }]
          });

          this.mapChart.on('click', (params) => {
            if (params.seriesType === 'map3D' && params.name) {
              this.drillToCity(params.name);
            }
          });
        })
        .catch(err => {
          console.error('地图数据加载失败:', err);
        });
    },

    drillToCity(cityName) {
      this.isCityMode = true;
      this.currentCityName = cityName.replace(/市/g, '');

      const echartsDiv = document.getElementById('echarts');
      const gaodeDiv = document.getElementById('gaode');

      if (echartsDiv) echartsDiv.style.opacity = '0';
      if (gaodeDiv) {
        gaodeDiv.style.opacity = '1';
        gaodeDiv.style.zIndex = '2';
      }

      const isMunicipality = this.provinceName.includes('市');

      let cityForApi;
      let shouldFetchAllDistricts = true;
      let targetDistrictName = '';

      if (isMunicipality) {
        if (cityName === this.provinceName) {
          cityForApi = this.provinceName;
          shouldFetchAllDistricts = true;
          targetDistrictName = '';
        } else {
          cityForApi = this.provinceName + cityName;
          shouldFetchAllDistricts = false;
          targetDistrictName = cityName.replace(/市/g, '').trim();
        }
      } else {
        const cleanCityName = cityName
          .replace(/(白族|傣族|彝族|哈尼族|壮族|苗族|回族|瑶族|僳族|拉祜族|布朗族|景颇族|阿昌族|德昂族|侗族|土家族)(自治)?州/g, '')
          .replace(/市/g, '')
          .trim();
        cityForApi = cleanCityName;
        targetDistrictName = '';
      }

      const apiUrl = `https://restapi.amap.com/v3/geocode/geo?address=${encodeURIComponent(cityForApi)}&key=${this.gaodeApiKey}`;

      fetch(apiUrl)
        .then(res => res.json())
        .then(data => {
          if (data.status === '1' && data.geocodes && data.geocodes.length > 0) {
            const location = data.geocodes[0].location;
            this.currentLocation = location;

            setTimeout(() => {
              if (echartsDiv) echartsDiv.style.zIndex = '0';
              this.initGaodeMap(cityForApi, location, shouldFetchAllDistricts, targetDistrictName);
            }, 800);
          } else {
            console.error('❌ 高德 API 返回错误:', data);
            alert('获取城市位置失败');
          }
        })
        .catch(err => {
          console.error('❌ 高德 API 请求失败:', err);
          alert('获取城市位置失败');
        });
    },


    initGaodeMap(cityName, location, shouldFetchAllDistricts = true, districtName = '') {
      const dom = document.getElementById('gaode');
      if (!dom) return;

      if (window.AMap) {
        this.createGaodeMap(cityName, location, shouldFetchAllDistricts, districtName);
      } else {
        const script = document.createElement('script');
        script.src = `https://webapi.amap.com/maps?v=1.4.15&key=${this.gaodeApiKey}`;
        script.onload = () => {
          this.createGaodeMap(cityName, location, shouldFetchAllDistricts, districtName);
        };
        document.head.appendChild(script);
      }
    },

     createGaodeMap(cityName, location, shouldFetchAllDistricts = true, districtName = '') {
      const [lng, lat] = location.split(',').map(Number);

      // 销毁旧地图实例，防止冲突
      if (this.gaodeMap) {
        this.gaodeMap.destroy();
      }

      this.gaodeMap = new AMap.Map('gaode', {
        center: [lng, lat],
        zoom: 11,
        viewMode: '2D',
        resizeEnable: true
      });

      // 移除旧的zoomchange监听器，防止Vite HMR热更新导致重复绑定
      this.gaodeMap.off('zoomchange');
      this.gaodeMap.on('zoomchange', () => {
        const zoom = this.gaodeMap.getZoom();
        if (zoom < 11) {
          // 缩小到11以下：切回绿泡泡，清掉小区长条数据
          this.districtMarkers.forEach(m => m.setMap(this.gaodeMap));
          this.clearMarkers(this.communityMarkers);
        }
      });

      if (shouldFetchAllDistricts) {
        const cityForDistrictApi = this.provinceName.includes('市') ? this.provinceName : cityName.replace(/市/g, '').trim();
        this.fetchCityDistrictData(cityForDistrictApi);
      } else {
        this.fetchSingleDistrictData(this.provinceName, districtName);
      }
    },


    async fetchCityDistrictData(cityName) {
      try {
        const response = await request.get('/analysis/api/city-district-detail/', {
          params: { city: cityName }
        });

        if (response.data && response.data.districts) {
          this.renderDistrictBubbles(response.data.districts);
        }
      } catch (err) {
        console.error('获取区县数据失败:', err);
      }
    },
    async fetchSingleDistrictData(city, district) {

      try {
        // 确保直辖市传入完整名称
        const cityParam = city.includes('市') ? city : city + '市';
        const response = await request.get('/analysis/api/city-district-detail/', {
          params: { city: cityParam }
        });

        if (response.data && response.data.districts) {
          const cleanDistrict = district.replace(/自治|白族|彝族|壮族|苗族|回族|维吾尔族|市|区|新区|县|镇|乡/g, '').trim();

          const singleDistrict = response.data.districts.filter(d => {
            const dName = d.name || '';
            const cleanJsonName = dName.replace(/自治|白族|彝族|壮族|苗族|回族|维吾尔族|市|区|新区|县|镇|乡/g, '').trim();

            const match = cleanJsonName === cleanDistrict || dName === district;
            return match;
          });

          if (singleDistrict.length > 0) {
            this.renderDistrictBubbles(singleDistrict);
          } else {
            const fallback = response.data.districts.filter(d => d.name.includes(district));
            if (fallback.length > 0) {
               this.renderDistrictBubbles(fallback);
            }
          }
        }
      } catch (err) {
        console.error('❌ 获取区县数据失败:', err);
      }
    },


    async showHouseModal(item) {
      this.currentCommunity = item.community_name;
      this.houseList = [];
      this.showModal = true;

      let cityForApi;
      if (this.provinceName.includes('市')) {
        cityForApi = this.provinceName;
      } else {
        cityForApi = this.currentCityName;
      }

      const districtName = item.district || item.extData?.district || this.currentDistrictName || '';

      try {
        const res = await request.get('/analysis/api/house-details/', {
          params: {
            city: cityForApi,
            district: districtName,
            community: item.community_name
          }
        });
        this.houseList = res.data.houses || [];
      } catch (e) {
        console.error('获取房源列表失败:', e);
        alert('获取数据失败，请检查控制台');
      }
    },

    closeModal() {
      this.showModal = false;
    },
    handleImageError(e) {
      e.target.src = 'https://via.placeholder.com/150'; // 图片加载失败时的占位图
    },
    renderDistrictBubbles(districts) {
      if (!this.gaodeMap) return;

      // 1. 清空旧的标记
      this.clearMarkers(this.districtMarkers);
      this.currentDistricts = districts;

      districts.forEach(district => {
        if (!district.lng || !district.lat) return;

        const countDisplay = district.count >= 10000
          ? (district.count / 10000).toFixed(2) + '万套'
          : district.count + '套';
        const priceDisplay = Math.round(district.avg_price) + '元';

        const content = `
          <div style="
            background: #00b359; color: white; padding: 10px 14px; border-radius: 50%;
            width: 80px; height: 80px; display: flex; flex-direction: column;
            align-items: center; justify-content: center; text-align: center;
            box-shadow: 0 4px 12px rgba(0, 179, 89, 0.4); border: 2px solid rgba(255, 255, 255, 0.3);
            font-size: 11px; line-height: 1.4; cursor: pointer; transition: transform 0.3s;
          " onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
            <div style="font-weight: bold; font-size: 13px; margin-bottom: 3px;">${district.name.replace('区', '')}</div>
            <div style="font-size: 12px;">${priceDisplay}</div>
            <div style="font-size: 10px; opacity: 0.9;">${countDisplay}</div>
          </div>
        `;

        const marker = new AMap.Marker({
          position: [district.lng, district.lat],
          content: content,
          offset: new AMap.Pixel(-40, -40),
          // 不要在这里写 map: this.gaodeMap，由下面的 setMap 控制
          extData: {
            districtName: district.name,
            cityName: this.currentCityName
          }
        });

        // 点击区县气泡触发下钻
        marker.on('click', () => {
          this.drillToDistrict({
            ...district,
            extData: {
              cityName: this.currentCityName.replace(/市/g, ''),
              districtName: district.name // 传递带"区"字的名称
            }
          });
        });

        this.districtMarkers.push(marker);
      });

      // 2. 如果是“区县视图”模式，手动把气泡显示在地图上
      if (!this.isCommunityView) {
        this.districtMarkers.forEach(m => m.setMap(this.gaodeMap));
      }
    },

       drillToDistrict(district) {
      if (!this.gaodeMap) return;

      this.isCommunityView = true;
      this.currentDistrictName = district.extData.districtName;

      // 隐藏绿泡泡
      this.districtMarkers.forEach(m => m.setMap(null));

      let cityForApi;
      if (this.provinceName.includes('市')) {
        cityForApi = this.provinceName;
      } else {
        cityForApi = district.extData.cityName;
      }
      const districtForApi = district.extData.districtName;

      // 先加载数据，加载完后自动 fitView 居中显示小区长条
      this.fetchCommunityData(cityForApi, districtForApi).then(() => {
        if (this.communityMarkers.length > 0) {
          this.gaodeMap.setFitView(this.communityMarkers, false, 80);
        }
      });
    },


    showCommunityLevel(cityName) {
      if (this.communityMarkers.length > 0) {
        this.switchMarkers(true);
        return;
      }

      if (this.apiData && this.apiData.districts) {
        this.apiData.districts.forEach(d => {
          this.fetchCommunityData(cityName, d.name);
        });
      }
      this.switchMarkers(true);
    },

    async fetchCommunityData(city, district) {
      this.clearMarkers(this.communityMarkers);
      try {
        const res = await request.get('/analysis/api/community-detail/', {
          params: { city, district }
        });
        if (res.data.communities) {
          this.renderCommunityBubbles(res.data.communities);
        }
      } catch (e) { console.error(e); }
    },


       renderCommunityBubbles(communities) {
      // 1. 清除旧的小区标签
      this.clearMarkers(this.communityMarkers);

      if (!communities || communities.length === 0) {
        console.warn('⚠️ 当前区县没有小区数据');
        return;
      }

      communities.forEach(item => {
        // 2. 使用 item 的数据，而不是 district
        const priceDisplay = (item.avg_price / 10000).toFixed(2) + '万';
        const countDisplay = item.count + '套';

        const content = `
          <div style="
            display: flex; align-items: center; background: #00b359;
            color: white; padding: 4px 12px 4px 8px; border-radius: 20px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.2); white-space: nowrap;
            font-size: 12px; cursor: pointer;
          ">
            <div style="margin-right: 8px;">${item.community_name} | ${countDisplay}</div>
            <div style="
              background: rgba(255,255,255,0.9); color: #00b359;
              padding: 2px 8px; border-radius: 12px; font-weight: bold;
            ">
              ${priceDisplay}
            </div>
          </div>
        `;

        // 3. 创建 Marker：使用 item.lng 和 item.lat
        const marker = new AMap.Marker({
          position: [item.lng, item.lat],
          content: content,
          offset: new AMap.Pixel(-60, -15),
          map: this.gaodeMap, // 直接显示在地图上
          extData: item
        });

        // 4. 绑定点击事件
        marker.on('click', () => {
          this.showHouseModal(item);
        });

        this.communityMarkers.push(marker);
      });
    },




    switchMarkers(showCommunity) {
      const zoom = this.gaodeMap.getZoom();
      if (zoom >= 11) {
        this.districtMarkers.forEach(m => m.setMap(null));
        this.communityMarkers.forEach(m => m.setMap(this.gaodeMap));
      } else {
        this.districtMarkers.forEach(m => m.setMap(this.gaodeMap));
        this.communityMarkers.forEach(m => m.setMap(null));
      }
    },

    clearMarkers(markers) {
      markers.forEach(m => m.setMap(null));
      markers.length = 0;
    },

    initCityTopChart() {
      const dom = this.$refs.cityTopChart;
      if (!dom || !this.apiData) return;
      this.cityTopChart = echarts.init(dom);
      const tooltipEl = this.$refs.cityTopTooltip;
      const sorted = [...this.apiData.districts].sort((a, b) => b.count - a.count);
      const showCount = 5;
      const maxXValue = sorted.length > 0 ? sorted[0].count : 100;
      const displayData = [...sorted, ...sorted.slice(0, showCount)];
      let currentIndex = 0;
      this.cityTopIsHovering = false;

      const updateChart = () => {
        if (this.cityTopIsHovering) return;
        const currentData = displayData.slice(currentIndex, currentIndex + showCount);
        this.cityTopChart.setOption({
          tooltip: { show: false },
          grid: { left: '15%', right: '12%', top: '5%', bottom: '15%' },
          xAxis: { type: 'value', splitLine: { show: false }, max: maxXValue * 1.1, axisLabel: { color: '#fff' } },
          yAxis: { type: 'category', data: currentData.map(d => d.name).reverse(), axisLabel: { color: '#fff' } },
          series: [{
            type: 'bar',
            data: currentData.map(d => d.count).reverse(),
            barWidth: '50%',
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#00d4ff' }, { offset: 1, color: '#00ffff' }])
            }
          }]
        });
        currentIndex++;
        if (currentIndex >= sorted.length) currentIndex = 0;
      };
      updateChart();
      if (this.cityTopTimer) clearInterval(this.cityTopTimer);
      this.cityTopTimer = setInterval(updateChart, 2000);

      this.cityTopChart.getZr().on('mousemove', () => {
        if (this.cityTopTimer) { clearInterval(this.cityTopTimer); this.cityTopTimer = null; }
      });

      this.cityTopChart.on('mouseover', (params) => {
        if (params.componentType !== 'series') return;
        const option = this.cityTopChart.getOption();
        let html = '<div style="font-weight:bold;margin-bottom:4px;">' + params.name + '</div>';
        html += '<div>房源数量：' + params.value + '套</div>';
        tooltipEl.innerHTML = html;
        tooltipEl.style.display = 'block';
      });
      this.cityTopChart.on('globalout', () => {
        tooltipEl.style.display = 'none';
        if (!this.cityTopTimer) this.cityTopTimer = setInterval(updateChart, 2000);
      });

      dom.addEventListener('mousemove', (e) => {
        if (tooltipEl.style.display === 'block') {
          const rect = dom.getBoundingClientRect();
          const tooltipH = tooltipEl.offsetHeight || 60;
          const tooltipW = tooltipEl.offsetWidth || 160;
          let left = e.clientX - rect.left + 15;
          let top = e.clientY - rect.top - tooltipH - 10;
          if (left + tooltipW > rect.width) left = e.clientX - rect.left - tooltipW - 15;
          if (top < 0) top = e.clientY - rect.top + 15;
          tooltipEl.style.left = left + 'px';
          tooltipEl.style.top = top + 'px';
        }
      });
    },

    initPriceDistChart() {
      const dom = this.$refs.priceDistChart;
      if (!dom || !this.apiData) return;
      this.priceDistChart = echarts.init(dom);
      const tooltipEl = this.$refs.priceDistTooltip;
      const priceRaw = this.apiData.price_distribution || [];
      const mergedPrice = { '0-1000': 0, '1000-2000': 0, '2000-3000': 0, '3000+': 0 };
      priceRaw.forEach(item => {
        const range = item.range;
        if (range.includes('0-1000') || range === '0-500' || range === '500-1000') mergedPrice['0-1000'] += item.count;
        else if (range.includes('1000-2000') || range === '1000-1500' || range === '1500-2000') mergedPrice['1000-2000'] += item.count;
        else if (range.includes('2000-3000') || range === '2000-2500' || range === '2500-3000') mergedPrice['2000-3000'] += item.count;
        else mergedPrice['3000+'] += item.count;
      });
      const priceData = Object.entries(mergedPrice).map(([range, count]) => ({ range, count }));
      const showCount = 3;
      this.priceDistStartIndex = 0;
      this.priceDistIsHovering = false;

      const updateChart = () => {
        if (this.priceDistIsHovering) return;
        let currentData;
        if (this.priceDistStartIndex <= priceData.length - showCount) {
          currentData = priceData.slice(this.priceDistStartIndex, this.priceDistStartIndex + showCount);
        } else {
          const remaining = priceData.length - this.priceDistStartIndex;
          const needFromStart = showCount - remaining;
          currentData = [...priceData.slice(this.priceDistStartIndex), ...priceData.slice(0, needFromStart)];
        }
        this.priceDistChart.setOption({
          tooltip: { show: false },
          grid: { left: '12%', right: '5%', top: '10%', bottom: '15%' },
          xAxis: { type: 'category', data: currentData.map(d => d.range), axisLabel: { color: '#fff', interval: 0 } },
          yAxis: { type: 'value', splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }, axisLabel: { color: '#fff' } },
          series: [{
            type: 'bar',
            data: currentData.map(d => d.count),
            barWidth: '40%',
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#00ffff' }, { offset: 1, color: '#00d4ff' }])
            }
          }]
        });
        this.priceDistStartIndex++;
        if (this.priceDistStartIndex >= priceData.length) this.priceDistStartIndex = 0;
      };
      updateChart();
      if (this.priceDistTimer) clearInterval(this.priceDistTimer);
      this.priceDistTimer = setInterval(updateChart, 2000);

      this.priceDistChart.getZr().on('mousemove', () => {
        if (this.priceDistTimer) { clearInterval(this.priceDistTimer); this.priceDistTimer = null; }
      });
      this.priceDistChart.on('mouseover', (params) => {
        if (params.componentType !== 'series') return;
        tooltipEl.innerHTML = '<div style="font-weight:bold;margin-bottom:4px;">' + params.name + '(元)</div><div>房源数量：' + params.value + '套</div>';
        tooltipEl.style.display = 'block';
      });
      this.priceDistChart.on('globalout', () => {
        tooltipEl.style.display = 'none';
        if (!this.priceDistTimer) this.priceDistTimer = setInterval(updateChart, 2000);
      });
      dom.addEventListener('mousemove', (e) => {
        if (tooltipEl.style.display === 'block') {
          const rect = dom.getBoundingClientRect();
          let left = e.clientX - rect.left + 15;
          let top = e.clientY - rect.top - 50;
          if (left + 160 > rect.width) left = e.clientX - rect.left - 175;
          if (top < 0) top = e.clientY - rect.top + 15;
          tooltipEl.style.left = left + 'px';
          tooltipEl.style.top = top + 'px';
        }
      });
    },

    initAreaDistChart() {
      const dom = this.$refs.areaDistChart;
      if (!dom || !this.apiData) return;
      this.areaDistChart = echarts.init(dom);
      const tooltipEl = this.$refs.areaDistTooltip;
      const areaRaw = this.apiData.area_distribution || [];
      const mergedArea = { '0-50': 0, '50-80': 0, '80-120': 0, '120+': 0 };
      areaRaw.forEach(item => {
        const range = item.range;
        if (range.includes('0-50') || range === '0-30' || range === '30-50') mergedArea['0-50'] += item.count;
        else if (range.includes('50-80') || range === '50-60' || range === '60-80') mergedArea['50-80'] += item.count;
        else if (range.includes('80-120') || range === '80-100' || range === '100-120') mergedArea['80-120'] += item.count;
        else mergedArea['120+'] += item.count;
      });
      const areaData = Object.entries(mergedArea).map(([range, count]) => ({ range, count }));
      const showCount = 3;
      this.areaDistStartIndex = 0;
      this.areaDistIsHovering = false;

      const updateChart = () => {
        if (this.areaDistIsHovering) return;
        let currentData;
        if (this.areaDistStartIndex <= areaData.length - showCount) {
          currentData = areaData.slice(this.areaDistStartIndex, this.areaDistStartIndex + showCount);
        } else {
          const remaining = areaData.length - this.areaDistStartIndex;
          const needFromStart = showCount - remaining;
          currentData = [...areaData.slice(this.areaDistStartIndex), ...areaData.slice(0, needFromStart)];
        }
        this.areaDistChart.setOption({
          tooltip: { show: false },
          grid: { left: '12%', right: '5%', top: '10%', bottom: '15%' },
          xAxis: { type: 'category', data: currentData.map(d => d.range), axisLabel: { color: '#fff', interval: 0 } },
          yAxis: { type: 'value', splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }, axisLabel: { color: '#fff' } },
          series: [{
            type: 'bar',
            data: currentData.map(d => d.count),
            barWidth: '40%',
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#00ffff' }, { offset: 1, color: '#00d4ff' }])
            }
          }]
        });
        this.areaDistStartIndex++;
        if (this.areaDistStartIndex >= areaData.length) this.areaDistStartIndex = 0;
      };
      updateChart();
      if (this.areaDistTimer) clearInterval(this.areaDistTimer);
      this.areaDistTimer = setInterval(updateChart, 2000);

      this.areaDistChart.getZr().on('mousemove', () => {
        if (this.areaDistTimer) { clearInterval(this.areaDistTimer); this.areaDistTimer = null; }
      });
      this.areaDistChart.on('mouseover', (params) => {
        if (params.componentType !== 'series') return;
        tooltipEl.innerHTML = '<div style="font-weight:bold;margin-bottom:4px;">' + params.name + '(m²)</div><div>房源数量：' + params.value + '套</div>';
        tooltipEl.style.display = 'block';
      });
      this.areaDistChart.on('globalout', () => {
        tooltipEl.style.display = 'none';
        if (!this.areaDistTimer) this.areaDistTimer = setInterval(updateChart, 2000);
      });
      dom.addEventListener('mousemove', (e) => {
        if (tooltipEl.style.display === 'block') {
          const rect = dom.getBoundingClientRect();
          let left = e.clientX - rect.left + 15;
          let top = e.clientY - rect.top - 50;
          if (left + 160 > rect.width) left = e.clientX - rect.left - 175;
          if (top < 0) top = e.clientY - rect.top + 15;
          tooltipEl.style.left = left + 'px';
          tooltipEl.style.top = top + 'px';
        }
      });
    },

    initRentTypeChart() {
      const dom = this.$refs.rentTypeChart;
      if (!dom || !this.apiData) return;
      this.rentTypeChart = echarts.init(dom);
      const rentTypeRaw = this.apiData.rent_type_distribution || [];
      const mergedRentType = {};
      rentTypeRaw.forEach(item => {
        const type = item.type;
        if (type.includes('整租')) mergedRentType['整租'] = (mergedRentType['整租'] || 0) + item.count;
        else if (type.includes('合租')) mergedRentType['合租'] = (mergedRentType['合租'] || 0) + item.count;
        else mergedRentType[type] = (mergedRentType[type] || 0) + item.count;
      });
      const totalRent = Object.values(mergedRentType).reduce((a, b) => a + b, 0);
      const rentData = Object.entries(mergedRentType).map(([name, value]) => ({
        name, value, percent: ((value / totalRent) * 100).toFixed(2)
      }));
      this.rentTypeChart.setOption({
        tooltip: { trigger: 'item', formatter: params => `${params.name}<br/>数量：${params.value}(套)<br/>占比：${params.percent}%` },
        legend: { orient: 'vertical', right: '5%', top: 'center', textStyle: { color: '#fff' } },
        series: [{
          type: 'pie', radius: ['40%', '70%'], center: ['40%', '50%'], avoidLabelOverlap: false,
          itemStyle: { borderRadius: 5, borderColor: '#0a1929', borderWidth: 2 },
          label: { show: true, position: 'outside', formatter: '{d}%', color: '#fff', fontSize: 14 },
          labelLine: { show: true, length: 15, length2: 10 },
          data: rentData.map((item, index) => ({
            value: item.value, name: item.name,
            itemStyle: { color: ['#00d4ff', '#00ffff', '#11b4da', '#0099cc'][index % 4] }
          }))
        }]
      });
    },

    initTopPriceChart() {
      const dom = this.$refs.topPriceChart;
      if (!dom || !this.apiData) return;
      this.topPriceChart = echarts.init(dom);
      const tooltipEl = this.$refs.topPriceTooltip;
      const top5 = this.apiData.top5_max_price || [];
      const showCount = 4;
      this.topPriceStartIndex = 0;
      this.topPriceIsHovering = false;

      const updateChart = () => {
        if (this.topPriceIsHovering) return;
        let currentData;
        if (this.topPriceStartIndex <= top5.length - showCount) {
          currentData = top5.slice(this.topPriceStartIndex, this.topPriceStartIndex + showCount);
        } else {
          const remaining = top5.length - this.topPriceStartIndex;
          const needFromStart = showCount - remaining;
          currentData = [...top5.slice(this.topPriceStartIndex), ...top5.slice(0, needFromStart)];
        }
        this.topPriceChart.setOption({
          tooltip: { show: false },
          grid: { left: '15%', right: '5%', top: '10%', bottom: '20%' },
          xAxis: { type: 'category', data: currentData.map(d => d.name), axisLabel: { color: '#fff', rotate: 30, interval: 0 } },
          yAxis: { type: 'value', splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }, axisLabel: { color: '#fff' } },
          series: [{
            type: 'bar', data: currentData.map(d => d.max_price), barWidth: '40%',
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#00ffff' }, { offset: 1, color: '#00d4ff' }])
            }
          }]
        });
        this.topPriceStartIndex++;
        if (this.topPriceStartIndex >= top5.length) this.topPriceStartIndex = 0;
      };
      updateChart();
      if (this.topPriceTimer) clearInterval(this.topPriceTimer);
      this.topPriceTimer = setInterval(updateChart, 2000);

      this.topPriceChart.getZr().on('mousemove', () => {
        if (this.topPriceTimer) { clearInterval(this.topPriceTimer); this.topPriceTimer = null; }
      });
      this.topPriceChart.on('mouseover', (params) => {
        if (params.componentType !== 'series') return;
        tooltipEl.innerHTML = '<div style="font-weight:bold;margin-bottom:4px;">' + params.name + '</div><div>最高租金：¥' + params.value + '(元/月)</div>';
        tooltipEl.style.display = 'block';
      });
      this.topPriceChart.on('globalout', () => {
        tooltipEl.style.display = 'none';
        if (!this.topPriceTimer) this.topPriceTimer = setInterval(updateChart, 2000);
      });
      dom.addEventListener('mousemove', (e) => {
        if (tooltipEl.style.display === 'block') {
          const rect = dom.getBoundingClientRect();
          let left = e.clientX - rect.left + 15;
          let top = e.clientY - rect.top - 50;
          if (left + 160 > rect.width) left = e.clientX - rect.left - 175;
          if (top < 0) top = e.clientY - rect.top + 15;
          tooltipEl.style.left = left + 'px';
          tooltipEl.style.top = top + 'px';
        }
      });
    },

    initAvgPriceChart() {
      const dom = this.$refs.avgPriceChart;
      if (!dom || !this.apiData) return;
      this.avgPriceChart = echarts.init(dom);
      const tooltipEl = this.$refs.avgPriceTooltip;
      const districts = this.apiData.districts.slice(0, 6);
      const showCount = 4;
      this.avgPriceStartIndex = 0;
      this.avgPriceIsHovering = false;

      const updateChart = () => {
        if (this.avgPriceIsHovering) return;
        let currentData;
        if (this.avgPriceStartIndex <= districts.length - showCount) {
          currentData = districts.slice(this.avgPriceStartIndex, this.avgPriceStartIndex + showCount);
        } else {
          const remaining = districts.length - this.avgPriceStartIndex;
          const needFromStart = showCount - remaining;
          currentData = [...districts.slice(this.avgPriceStartIndex), ...districts.slice(0, needFromStart)];
        }
        this.avgPriceChart.setOption({
          tooltip: { show: false },
          legend: { top: '5%', textStyle: { color: '#fff' } },
          grid: { left: '12%', right: '12%', top: '20%', bottom: '15%' },
          xAxis: { type: 'category', data: currentData.map(d => d.name), axisLabel: { color: '#fff', rotate: 20, interval: 0 } },
          yAxis: [
            { type: 'value', splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }, axisLabel: { color: '#fff' } },
            { type: 'value', splitLine: { show: false }, axisLabel: { color: '#fff' } }
          ],
          series: [
            { name: '均价', type: 'bar', data: currentData.map(d => d.avg_price), barWidth: '30%', itemStyle: { color: '#00d4ff' } },
            { name: '均面积', type: 'line', yAxisIndex: 1, data: currentData.map(d => d.avg_area), lineStyle: { color: '#00ffff', width: 2 }, itemStyle: { color: '#00ffff' } }
          ]
        });
        this.avgPriceStartIndex++;
        if (this.avgPriceStartIndex >= districts.length) this.avgPriceStartIndex = 0;
      };
      updateChart();
      if (this.avgPriceTimer) clearInterval(this.avgPriceTimer);
      this.avgPriceTimer = setInterval(updateChart, 2000);

      this.avgPriceChart.getZr().on('mousemove', () => {
        if (this.avgPriceTimer) { clearInterval(this.avgPriceTimer); this.avgPriceTimer = null; }
      });
      this.avgPriceChart.on('mouseover', (params) => {
        if (params.componentType !== 'series') return;
        const option = this.avgPriceChart.getOption();
        const idx = params.dataIndex;
        let html = '<div style="font-weight:bold;margin-bottom:4px;">' + params.name + '</div>';
        html += '<div>均价：¥' + option.series[0].data[idx] + '(元/月)</div>';
        html += '<div>均面积：' + option.series[1].data[idx] + '(m²)</div>';
        tooltipEl.innerHTML = html;
        tooltipEl.style.display = 'block';
      });
      this.avgPriceChart.on('globalout', () => {
        tooltipEl.style.display = 'none';
        if (!this.avgPriceTimer) this.avgPriceTimer = setInterval(updateChart, 2000);
      });
      dom.addEventListener('mousemove', (e) => {
        if (tooltipEl.style.display === 'block') {
          const rect = dom.getBoundingClientRect();
          let left = e.clientX - rect.left + 15;
          let top = e.clientY - rect.top - 50;
          if (left + 160 > rect.width) left = e.clientX - rect.left - 175;
          if (top < 0) top = e.clientY - rect.top + 15;
          tooltipEl.style.left = left + 'px';
          tooltipEl.style.top = top + 'px';
        }
      });
    }
  }
}
</script>

<style scoped>
.detail-screen {
  width: 100vw;
  height: 100vh;
  background: transparent;
  color: #fff;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  position: relative;
}
.detail-header {
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
  background: linear-gradient(to bottom, rgba(0, 50, 100, 0.6), transparent);
  border-bottom: 1px solid rgba(0, 212, 255, 0.3);
}

.back-btn-group {
  display: flex;
  gap: 10px;
}

.back-btn {
  cursor: pointer;
  padding: 8px 16px;
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 4px;
  color: #00d4ff;
  font-size: 14px;
}

.title-box {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-decoration {
  width: 150px;
  height: 25px;
}

.title {
  font-size: 26px;
  font-weight: bold;
  color: #00d4ff;
  text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
  letter-spacing: 3px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.info-value {
  font-size: 18px;
  color: #00d4ff;
  font-weight: bold;
}

.detail-content {
  flex: 1;
  display: flex;
  padding: 15px;
  gap: 15px;
  height: calc(100vh - 70px);
  position: relative;
  z-index: 1;
}

.left-column, .right-column {
  flex: 0 0 22%;
  display: flex;
  flex-direction: column;
  gap: 15px;
  position: relative;
  z-index: 2;
}

.center-map {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.map-box {
  width: 100%;
  height: 100%;
  padding: 0;
  position: absolute;
  top: 0;
  left: 0;
  z-index: 0;
  border: none;
}

/* 新增的地图容器样式 */
.map-container {
  position: relative;
  width: 100%;
  height: 100%;
}

.map-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  transition: opacity 0.8s ease-in-out;
}

#province-map {
  width: 100%;
  height: 100%;
}

.chart-box {
  flex: 1;
  position: relative;
  background: rgba(10, 25, 41, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 8px;
  z-index: 2;
}

.box {
  width: 100%;
  height: 100%;
  padding: 10px;
}

.box-header {
  font-size: 15px;
  color: #00d4ff;
  font-weight: bold;
  margin-bottom: 10px;
  padding-left: 10px;
}

.chart-container {
  position: relative;
  width: 100%;
  height: calc(100% - 30px);
}


.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.6); z-index: 9999;
  display: flex; justify-content: center; align-items: center;
}
.modal-content {
  background: #0b1829; border: 1px solid #00d4ff; border-radius: 8px;
  width: 500px; max-height: 80vh; display: flex; flex-direction: column;
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}
.modal-header {
  padding: 15px 20px; border-bottom: 1px solid #1c3a5e;
  display: flex; justify-content: space-between; align-items: center;
}
.modal-header h3 { color: #00d4ff; margin: 0; font-size: 18px; }
.close-btn { color: #fff; font-size: 24px; cursor: pointer; }
.modal-body {
  padding: 20px; overflow-y: auto; flex: 1;
}
.house-item {
  display: flex; background: #0f243d; margin-bottom: 15px; padding: 10px;
  border-radius: 4px; border: 1px solid #1c3a5e;
}
.house-img img { width: 120px; height: 90px; object-fit: cover; border-radius: 4px; }
.house-info { margin-left: 15px; flex: 1; color: #fff; }
.house-title { font-size: 16px; font-weight: bold; color: #fff; margin-bottom: 5px; }
.house-desc { font-size: 13px; color: #8fa3b8; margin-bottom: 5px; }
.house-price { color: #ffaa00; font-size: 18px; font-weight: bold; margin-bottom: 5px; }
.house-tags { margin-bottom: 5px; }
.tag {
  display: inline-block; background: #1c3a5e; color: #00d4ff;
  padding: 2px 6px; border-radius: 3px; font-size: 12px; margin-right: 5px;
}
.view-link { color: #00d4ff; text-decoration: underline; font-size: 13px; cursor: pointer; }

</style>
