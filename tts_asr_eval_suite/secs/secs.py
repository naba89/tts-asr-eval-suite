import torch
import torch.nn.functional as F
import torchaudio
from huggingface_hub import hf_hub_download

from resemblyzer import preprocess_wav

from tts_asr_eval_suite.secs.secs_ecapa2 import SECSEcapa2
from tts_asr_eval_suite.secs.secs_resemblyzer import SECSResemblyzer
from tts_asr_eval_suite.secs.secs_unispeech_ecapa_wavlm_large import SECSWavLMLargeSV
from tts_asr_eval_suite.secs.secs_wavlm_base_plus_sv import SECSWavLMBasePlusSV


class SECS:
    def __init__(self, device, methods) -> None:
        self.device = device
        self.sr = 16000
        if len(methods) == 0:
            methods = ['resemblyzer', 'wavlm_large_sv', 'wavlm_base_plus_sv', 'ecapa2']
        elif len(methods) == 1 and methods[0] == 'all':
            methods = ['resemblyzer', 'wavlm_large_sv', 'wavlm_base_plus_sv', 'ecapa2']

        self.scorers = {}
        for method in methods:
            if method == 'resemblyzer':
                self.scorers['resemblyzer'] = SECSResemblyzer(device)
            elif method == 'wavlm_large_sv':
                self.scorers['wavlm_large_sv'] = SECSWavLMLargeSV(device)
            elif method == 'wavlm_base_plus_sv':
                self.scorers['wavlm_base_plus_sv'] = SECSWavLMBasePlusSV(device)
            elif method == 'ecapa2':
                self.scorers['ecapa2'] = SECSEcapa2(device)
            else:
                raise ValueError(f"Invalid method: {method}")

    def __call__(self, prompt_path, gen_path):
        similarity = {}
        prompt_audio, sr_prompt = torchaudio.load(prompt_path)
        gen_audio, sr_gen = torchaudio.load(gen_path)

        prompt_audio = preprocess_wav(prompt_audio.squeeze().numpy(), source_sr=sr_prompt)
        gen_audio = preprocess_wav(gen_audio.squeeze().numpy(), source_sr=sr_gen)

        prompt_audio = torch.from_numpy(prompt_audio).to(self.device).unsqueeze(0)
        gen_audio = torch.from_numpy(gen_audio).to(self.device).unsqueeze(0)

        for method, scorer in self.scorers.items():
            similarity[f"SECS ({method})"] = scorer(prompt_audio, gen_audio)

        similarity[f"SECS (avg)"] = sum([similarity[f"SECS ({method})"] for method in self.scorers]) / len(self.scorers)
        return similarity
