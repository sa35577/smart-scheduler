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
        // print("🎤 [SpeechManager] startRecording() called")
        // Reset transcript for new rant
        transcript = ""
        isRecording = true
        // print("🎤 [SpeechManager] isRecording set to: \(isRecording), transcript: '\(transcript)'")
        
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
            
            // Don't process results if we've already stopped recording
            guard self.isRecording else {
                // print("⏭️ [SpeechManager] Ignoring recognition result - already stopped")
                return
            }
            
            if let result = result {
                // This updates your UI in real-time
                DispatchQueue.main.async {
                    // Double-check we're still recording before updating transcript
                    guard self.isRecording else {
                        // print("⏭️ [SpeechManager] Skipping transcript update - recording stopped")
                        return
                    }
                    let oldTranscript = self.transcript
                    self.transcript = result.bestTranscription.formattedString
                    // print("📝 [SpeechManager] Transcript updated: '\(oldTranscript)' -> '\(self.transcript)' (isFinal: \(result.isFinal))")
                }
            }
            
            if let error = error {
                // Don't log cancellation or "No speech detected" as errors - they're normal
                let errorDesc = error.localizedDescription
                // print("⚠️ [SpeechManager] Recognition callback error: \(errorDesc)")
                // print("⚠️ [SpeechManager] Current state - isRecording: \(self.isRecording), transcript length: \(self.transcript.count)")
                
                if !errorDesc.contains("canceled") && !errorDesc.contains("No speech detected") {
                    print("❌ Speech recognition error: \(errorDesc)")
                }
                // Only stop if we're still recording (prevents double-stop)
                DispatchQueue.main.async {
                    // print("🔄 [SpeechManager] Error callback - checking if should stop. isRecording: \(self.isRecording)")
                    if self.isRecording {
                        // print("🛑 [SpeechManager] Calling stopRecording() from error callback")
                        self.stopRecording()
                    } else {
                        // print("⏭️ [SpeechManager] Skipping stopRecording() - already stopped")
                    }
                }
            } else if result?.isFinal == true {
                // print("✅ [SpeechManager] Recognition final result received")
                // Only stop if we're still recording (prevents double-stop)
                DispatchQueue.main.async {
                    // print("🔄 [SpeechManager] Final result callback - checking if should stop. isRecording: \(self.isRecording)")
                    if self.isRecording {
                        // print("🛑 [SpeechManager] Calling stopRecording() from final result callback")
                        self.stopRecording()
                    } else {
                        // print("⏭️ [SpeechManager] Skipping stopRecording() - already stopped")
                    }
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
        // print("🛑 [SpeechManager] stopRecording() called")
        // print("🛑 [SpeechManager] Current state - isRecording: \(isRecording), transcript: '\(transcript)'")
        
        // Prevent multiple calls to stopRecording
        guard isRecording else {
            // print("⏭️ [SpeechManager] stopRecording() already called - skipping")
            return
        }
        
        // Preserve the current transcript before stopping
        let preservedTranscript = transcript
        // print("🛑 [SpeechManager] Preserving transcript: '\(preservedTranscript)'")
        
        // print("🛑 [SpeechManager] Setting isRecording to false")
        isRecording = false
        // print("🛑 [SpeechManager] isRecording is now: \(isRecording)")
        
        if audioEngine.isRunning {
            // print("🛑 [SpeechManager] Stopping audio engine")
            audioEngine.stop()
            audioEngine.inputNode.removeTap(onBus: 0)
        }
        
        // print("🛑 [SpeechManager] Ending recognition request and canceling task")
        recognitionRequest?.endAudio()
        recognitionRequest = nil
        recognitionTask?.cancel()
        recognitionTask = nil
        
        // Restore preserved transcript (in case callbacks cleared it)
        transcript = preservedTranscript
        // print("🛑 [SpeechManager] Restored transcript: '\(transcript)'")
        
        // Deactivate audio session
        try? AVAudioSession.sharedInstance().setActive(false)
        // print("🛑 [SpeechManager] stopRecording() complete - isRecording: \(isRecording), transcript: '\(transcript)'")
    }
}
