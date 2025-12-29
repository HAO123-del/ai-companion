/**
 * Audio Analyzer for Lip-Sync
 * Analyzes audio data to generate lip-sync amplitude values
 */

export class AudioAnalyzer {
  private audioContext: AudioContext | null = null
  private analyser: AnalyserNode | null = null
  private dataArray: Uint8Array | null = null
  private animationFrame: number | null = null
  private onAmplitudeChange: ((amplitude: number) => void) | null = null

  constructor() {
    // AudioContext will be created on first use
  }

  /**
   * Initialize the audio context and analyser
   */
  private init() {
    if (!this.audioContext) {
      this.audioContext = new AudioContext()
      this.analyser = this.audioContext.createAnalyser()
      this.analyser.fftSize = 256
      const bufferLength = this.analyser.frequencyBinCount
      this.dataArray = new Uint8Array(bufferLength)
    }
  }

  /**
   * Analyze audio from a base64 encoded string
   * Returns an array of amplitude values for lip-sync
   */
  async analyzeBase64Audio(base64Audio: string): Promise<number[]> {
    this.init()
    if (!this.audioContext || !this.analyser) return []

    try {
      // Decode base64 to array buffer
      const audioData = atob(base64Audio)
      const arrayBuffer = new ArrayBuffer(audioData.length)
      const view = new Uint8Array(arrayBuffer)
      for (let i = 0; i < audioData.length; i++) {
        view[i] = audioData.charCodeAt(i)
      }

      // Decode audio data
      const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer)
      
      // Generate amplitude data from audio buffer
      return this.generateAmplitudeData(audioBuffer)
    } catch (error) {
      console.error('Failed to analyze audio:', error)
      return []
    }
  }

  /**
   * Generate amplitude data from audio buffer
   * Samples the audio at regular intervals to create lip-sync data
   */
  private generateAmplitudeData(audioBuffer: AudioBuffer): number[] {
    const channelData = audioBuffer.getChannelData(0)
    const sampleRate = audioBuffer.sampleRate
    const duration = audioBuffer.duration
    
    // Sample every 50ms for lip-sync (20 frames per second)
    const frameInterval = 0.05
    const frameCount = Math.ceil(duration / frameInterval)
    const samplesPerFrame = Math.floor(sampleRate * frameInterval)
    
    const amplitudes: number[] = []
    
    for (let i = 0; i < frameCount; i++) {
      const startSample = i * samplesPerFrame
      const endSample = Math.min(startSample + samplesPerFrame, channelData.length)
      
      // Calculate RMS amplitude for this frame
      let sum = 0
      for (let j = startSample; j < endSample; j++) {
        sum += channelData[j] * channelData[j]
      }
      const rms = Math.sqrt(sum / (endSample - startSample))
      
      // Normalize to 0-1 range (typical speech RMS is around 0.1-0.3)
      const normalized = Math.min(1, rms * 5)
      amplitudes.push(normalized)
    }
    
    return amplitudes
  }

  /**
   * Start real-time audio analysis from microphone
   */
  async startMicrophoneAnalysis(onAmplitude: (amplitude: number) => void): Promise<void> {
    this.init()
    if (!this.audioContext || !this.analyser || !this.dataArray) return

    this.onAmplitudeChange = onAmplitude

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const source = this.audioContext.createMediaStreamSource(stream)
      source.connect(this.analyser)
      
      this.startAnalysisLoop()
    } catch (error) {
      console.error('Failed to access microphone:', error)
    }
  }

  /**
   * Start the analysis loop for real-time amplitude detection
   */
  private startAnalysisLoop() {
    if (!this.analyser || !this.dataArray) return
    
    const analyserNode = this.analyser
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const dataArr = this.dataArray as any

    const analyze = () => {
      analyserNode.getByteFrequencyData(dataArr)
      
      // Calculate average amplitude
      let sum = 0
      for (let i = 0; i < dataArr.length; i++) {
        sum += dataArr[i]
      }
      const average = sum / dataArr.length / 255
      
      if (this.onAmplitudeChange) {
        this.onAmplitudeChange(average)
      }
      
      this.animationFrame = requestAnimationFrame(analyze)
    }
    
    analyze()
  }

  /**
   * Stop real-time analysis
   */
  stopAnalysis() {
    if (this.animationFrame) {
      cancelAnimationFrame(this.animationFrame)
      this.animationFrame = null
    }
    this.onAmplitudeChange = null
  }

  /**
   * Clean up resources
   */
  dispose() {
    this.stopAnalysis()
    if (this.audioContext) {
      this.audioContext.close()
      this.audioContext = null
    }
    this.analyser = null
    this.dataArray = null
  }
}

// Singleton instance
export const audioAnalyzer = new AudioAnalyzer()
