//
//  SpeechManager.swift
//  smart-scheduler-fe
//
//  Created by Sat Arora on 2026-01-06.
//

import Foundation
import Speech
import AVFoundation
import Observation

@Observable
class SpeechManager {
    private var audioEngine = AVAudioEngine()
    private var speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    
    var transcript: String = ""
    var isRecording: Bool = false
    
    func startRecording() {
        // Reset transcript for new rant
        transcript = ""
        isRecording = true
        
        guard let speechRecognizer = speechRecognizer, speechRecognizer.isAvailable else {
            print("❌ Speech recognizer not available")
            isRecording = false
            return
        }
        
        // Request microphone permission
        AVAudioSession.sharedInstance().requestRecordPermission { [weak self] granted in
            guard granted else {
                print("❌ Microphone permission denied")
                DispatchQueue.main.async {
                    self?.isRecording = false
                }
                return
            }
            
            DispatchQueue.main.async {
                self?.startRecordingWithPermission()
            }
        }
    }
    
    private func startRecordingWithPermission() {
        guard let speechRecognizer = speechRecognizer, speechRecognizer.isAvailable else {
            isRecording = false
            return
        }
        
        // Stop and reset audio engine if already running
        if audioEngine.isRunning {
            audioEngine.stop()
            audioEngine.inputNode.removeTap(onBus: 0)
        }
        
        // Configure audio session for recording
        do {
            let audioSession = AVAudioSession.sharedInstance()
            try audioSession.setCategory(.record, mode: .measurement, options: .duckOthers)
            try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
            print("✅ Audio session configured")
        } catch {
            print("❌ Failed to configure audio session: \(error.localizedDescription)")
            isRecording = false
            return
        }
        
        audioEngine = AVAudioEngine()
        let newRequest = SFSpeechAudioBufferRecognitionRequest()
        recognitionRequest = newRequest
        
        guard let request = recognitionRequest else {
            print("❌ Recognition request is nil")
            isRecording = false
            return
        }
        
        let inputNode = audioEngine.inputNode
        request.shouldReportPartialResults = true
        
        recognitionTask = speechRecognizer.recognitionTask(with: request) { [weak self] result, error in
            guard let self = self else { return }
            
            if let result = result {
                // This updates your UI in real-time
                DispatchQueue.main.async {
                    self.transcript = result.bestTranscription.formattedString
                }
            }
            
            if let error = error {
                // Don't log "No speech detected" as an error - it's normal when user isn't speaking
                if !error.localizedDescription.contains("No speech detected") {
                    print("❌ Speech recognition error: \(error.localizedDescription)")
                }
                DispatchQueue.main.async {
                    self.stopRecording()
                }
            } else if result?.isFinal == true {
                DispatchQueue.main.async {
                    self.stopRecording()
                }
            }
        }
        
        // Prepare the audio engine first to get valid format
        audioEngine.prepare()
        
        // Get the input format after preparing - this is the hardware format
        let inputFormat = inputNode.outputFormat(forBus: 0)
        print("📊 Hardware input format: sampleRate=\(inputFormat.sampleRate), channels=\(inputFormat.channelCount)")
        
        // Validate the hardware format
        guard inputFormat.sampleRate > 0 && inputFormat.channelCount > 0 else {
            print("❌ Invalid hardware audio format: sampleRate=\(inputFormat.sampleRate), channels=\(inputFormat.channelCount)")
            isRecording = false
            recognitionRequest = nil
            recognitionTask = nil
            return
        }
        
        // Use the hardware format directly - it must match for installTap to work
        // Speech recognition will handle the format conversion internally
        print("✅ Using hardware format: sampleRate=\(inputFormat.sampleRate), channels=\(inputFormat.channelCount)")
        installTapWithFormat(inputFormat)
    }
    
    private func installTapWithFormat(_ format: AVAudioFormat) {
        let inputNode = audioEngine.inputNode
        
        do {
            inputNode.installTap(onBus: 0, bufferSize: 1024, format: format) { [weak self] buffer, _ in
                self?.recognitionRequest?.append(buffer)
            }
            
            try audioEngine.start()
            print("✅ Audio engine started successfully")
        } catch {
            print("❌ Failed to start audio engine: \(error.localizedDescription)")
            isRecording = false
            recognitionRequest = nil
            recognitionTask = nil
            
            // Deactivate audio session on error
            try? AVAudioSession.sharedInstance().setActive(false)
        }
    }
    
    func stopRecording() {
        if audioEngine.isRunning {
            audioEngine.stop()
            audioEngine.inputNode.removeTap(onBus: 0)
        }
        recognitionRequest?.endAudio()
        recognitionRequest = nil
        recognitionTask?.cancel()
        recognitionTask = nil
        
        // Deactivate audio session
        try? AVAudioSession.sharedInstance().setActive(false)
        
        isRecording = false
    }
}
