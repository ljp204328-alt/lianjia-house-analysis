<template>
  <div class="predict-page">
    <div class="predict-header">
      <button class="back-btn" @click="goBack">← 返回</button>
      <h1 class="page-title">租金价格智能预测</h1>
      <div class="model-info" v-if="modelInfo">
        模型准确率 R²: {{ (modelInfo.test_r2 * 100).toFixed(1) }}%
      </div>
    </div>

    <div class="predict-content">
      <div class="form-panel">
        <h2 class="panel-title">输入房源信息</h2>

        <div class="form-grid">
          <div class="form-item">
            <label>城市</label>
            <select v-model="form.city" @change="onCityChange">
              <option value="">请选择城市</option>
              <option v-for="c in options.city" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>

          <div class="form-item">
            <label>区县</label>
            <select v-model="form.district">
              <option value="">请选择区县</option>
              <option v-for="d in filteredDistricts" :key="d" :value="d">{{ d }}</option>
            </select>
          </div>

          <div class="form-item">
            <label>户型</label>
            <select v-model="form.house_type">
              <option value="">请选择户型</option>
              <option v-for="h in options.house_type" :key="h" :value="h">{{ h }}</option>
            </select>
          </div>

          <div class="form-item">
            <label>面积（㎡）</label>
            <input type="number" v-model.number="form.area" placeholder="请输入面积" min="1">
          </div>

          <div class="form-item">
            <label>朝向</label>
            <select v-model="form.direction">
              <option value="">请选择朝向</option>
              <option v-for="d in options.direction" :key="d" :value="d">{{ d }}</option>
            </select>
          </div>

          <div class="form-item">
            <label>楼层类型</label>
            <select v-model="form.floor_type">
              <option value="">请选择楼层类型</option>
              <option v-for="f in options.floor_type" :key="f" :value="f">{{ f }}</option>
            </select>
          </div>

          <div class="form-item">
            <label>租赁方式</label>
            <select v-model="form.rent_type">
              <option value="">请选择租赁方式</option>
              <option v-for="r in options.rent_type" :key="r" :value="r">{{ r }}</option>
            </select>
          </div>
        </div>

        <button class="predict-btn" @click="doPredict" :disabled="loading">
          {{ loading ? '预测中...' : '预测租金' }}
        </button>
      </div>

      <div class="result-panel">
        <h2 class="panel-title">预测结果</h2>

        <div v-if="result" class="result-card">
          <div class="result-price">
            <span class="price-num">{{ result.predicted_price }}</span>
            <span class="price-unit">元/月</span>
          </div>
          <div class="result-message">{{ result.message }}</div>

          <div class="result-detail">
            <div class="detail-item">
              <span class="detail-label">城市</span>
              <span class="detail-value">{{ form.city }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">区县</span>
              <span class="detail-value">{{ form.district }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">户型</span>
              <span class="detail-value">{{ form.house_type }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">面积</span>
              <span class="detail-value">{{ form.area }}㎡</span>
            </div>
          </div>
        </div>

        <div v-else class="result-empty">
          <div class="empty-icon">📊</div>
          <p>请填写左侧信息后点击"预测租金"</p>
        </div>

        <div v-if="modelInfo" class="model-stats">
          <h3>模型信息</h3>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-label">训练数据量</span>
              <span class="stat-value">{{ modelInfo.train_count }} 条</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">测试数据量</span>
              <span class="stat-value">{{ modelInfo.test_count }} 条</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">平均绝对误差</span>
              <span class="stat-value">{{ modelInfo.test_mae.toFixed(0) }} 元</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">决定系数 R²</span>
              <span class="stat-value">{{ (modelInfo.test_r2 * 100).toFixed(1) }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import request from '@/utils/request'

export default {
  name: 'PredictPage',
  data() {
    return {
      form: {
        city: '',
        district: '',
        house_type: '',
        area: null,
        direction: '',
        floor_type: '',
        rent_type: '整租'
      },
      options: {
        city: [],
        house_type: ['1室1厅1卫', '2室1厅1卫', '2室2厅1卫', '3室1厅1卫', '3室2厅1卫', '3室2厅2卫', '4室2厅2卫'],
        direction: ['南', '南北', '东南', '东', '西', '北', '西南', '东北'],
        floor_type: ['高楼层', '中楼层', '低楼层'],
        rent_type: ['整租', '合租']
      },
      allDistricts: {},
      result: null,
      modelInfo: null,
      loading: false
    }
  },
  computed: {
    filteredDistricts() {
      if (!this.form.city) return []
      return this.allDistricts[this.form.city] || []
    }
  },
  async mounted() {
    await this.loadModelInfo()
  },
  methods: {
    goBack() {
      this.$router.push('/home')
    },
    async loadModelInfo() {
      try {
        const res = await request.get('/analysis/api/rent-model-info/')
        this.modelInfo = res.data.model_info
        this.options.city = res.data.options.city || []
        this.allDistricts = res.data.city_district_map || {}
      } catch (err) {
        console.error('加载模型信息失败:', err)
      }
    },
    onCityChange() {
      this.form.district = ''
    },
    async doPredict() {
      if (!this.form.city || !this.form.district || !this.form.house_type ||
          !this.form.area || !this.form.direction || !this.form.floor_type ||
          !this.form.rent_type) {
        alert('请填写完整信息')
        return
      }

      this.loading = true
      this.result = null

      try {
        const res = await request.post('/analysis/api/rent-predict/', this.form)
        this.result = res.data
      } catch (err) {
        console.error('预测失败:', err)
        alert('预测失败: ' + (err.response?.data?.error || err.message))
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.predict-page {
  min-height: 100vh;
  background: radial-gradient(ellipse at bottom, #1B2735 0%, #090A0F 100%);
  color: #c7eaff;
  padding: 20px 40px;
}

.predict-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 30px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
}

.back-btn {
  background: rgba(0, 212, 255, 0.15);
  border: 1px solid rgba(0, 212, 255, 0.4);
  color: #00d4ff;
  padding: 8px 20px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.back-btn:hover {
  background: rgba(0, 212, 255, 0.3);
}

.page-title {
  font-size: 28px;
  color: #00d4ff;
  text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}

.model-info {
  font-size: 14px;
  color: #00ff88;
  background: rgba(0, 255, 136, 0.1);
  padding: 6px 14px;
  border-radius: 4px;
  border: 1px solid rgba(0, 255, 136, 0.3);
}

.predict-content {
  display: flex;
  gap: 30px;
}

.form-panel {
  flex: 1;
  background: rgba(0, 50, 100, 0.2);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  padding: 25px;
}

.result-panel {
  flex: 1;
  background: rgba(0, 50, 100, 0.2);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  padding: 25px;
}

.panel-title {
  font-size: 18px;
  color: #00d4ff;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}

.form-item label {
  display: block;
  font-size: 13px;
  color: #8cb8d8;
  margin-bottom: 6px;
}

.form-item select,
.form-item input {
  width: 100%;
  padding: 10px 12px;
  background: rgba(0, 20, 40, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 4px;
  color: #c7eaff;
  font-size: 14px;
  outline: none;
  transition: border-color 0.3s;
  box-sizing: border-box;
}

.form-item select:focus,
.form-item input:focus {
  border-color: #00d4ff;
  box-shadow: 0 0 8px rgba(0, 212, 255, 0.3);
}

.form-item select option {
  background: #0a1628;
  color: #c7eaff;
}

.predict-btn {
  width: 100%;
  margin-top: 25px;
  padding: 14px;
  background: linear-gradient(135deg, #00d4ff, #0099cc);
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s;
}

.predict-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 212, 255, 0.4);
}

.predict-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.result-card {
  text-align: center;
  padding: 20px 0;
}

.result-price {
  margin-bottom: 15px;
}

.price-num {
  font-size: 56px;
  font-weight: bold;
  color: #00ffff;
  text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
}

.price-unit {
  font-size: 18px;
  color: #8cb8d8;
  margin-left: 8px;
}

.result-message {
  font-size: 16px;
  color: #00ff88;
  margin-bottom: 25px;
}

.result-detail {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  text-align: left;
  background: rgba(0, 20, 40, 0.4);
  padding: 15px;
  border-radius: 6px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid rgba(0, 212, 255, 0.1);
}

.detail-label {
  color: #8cb8d8;
  font-size: 13px;
}

.detail-value {
  color: #c7eaff;
  font-size: 13px;
  font-weight: bold;
}

.result-empty {
  text-align: center;
  padding: 60px 0;
  color: #5a7a9a;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.model-stats {
  margin-top: 25px;
  padding-top: 20px;
  border-top: 1px solid rgba(0, 212, 255, 0.2);
}

.model-stats h3 {
  font-size: 15px;
  color: #8cb8d8;
  margin-bottom: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgba(0, 20, 40, 0.4);
  border-radius: 4px;
}

.stat-label {
  font-size: 12px;
  color: #5a7a9a;
}

.stat-value {
  font-size: 12px;
  color: #00d4ff;
  font-weight: bold;
}
</style>
