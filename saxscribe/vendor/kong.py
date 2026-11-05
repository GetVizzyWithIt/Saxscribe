"""Kong's high-resolution transcription model and its note decoder, vendored.

Source: Qiuqiang Kong, piano_transcription_inference (MIT licence), as forked
by Xavier Riley at github.com/xavriley/piano_transcription_inference @7568dc7
(models.py, utilities.py RegressionPostProcessor, piano_vad.py). Riley and
Dixon (2024) fine-tuned this model on Filosax; their checkpoint
(filosax_25k.pth) loads into Regress_onset_offset_frame_velocity_CRNN with
every weight matched.

Copied rather than installed because the package downloads a piano checkpoint
with wget and loads weights with torch's unsafe loader. Only the note path is
kept (no pedal model, no MIDI writer); the arithmetic is unchanged, including
the decoder's quirk that an onset in frame 0 is ignored, so results match the
package exactly.

MIT License, Copyright (c) 2020 Qiuqiang Kong. Permission is hereby granted,
free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to
the following conditions: The above copyright notice and this permission
notice shall be included in all copies or substantial portions of the
Software. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
"""
from __future__ import annotations

import math

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

SAMPLE_RATE = 16000
FRAMES_PER_SECOND = 100
CLASSES = 88
BEGIN_NOTE = 21          # MIDI number of class 0 (piano A0)
VELOCITY_SCALE = 128
SEGMENT_SAMPLES = SAMPLE_RATE * 10



def init_layer(layer):
    nn.init.xavier_uniform_(layer.weight)
    if getattr(layer, "bias", None) is not None:
        layer.bias.data.fill_(0.)


def init_bn(bn):
    bn.bias.data.fill_(0.)
    bn.weight.data.fill_(1.)


def init_gru(rnn):
    def concat_init(tensor, init_funcs):
        length, fan_out = tensor.shape
        fan_in = length // len(init_funcs)
        for i, init_func in enumerate(init_funcs):
            init_func(tensor[i * fan_in:(i + 1) * fan_in, :])

    def inner_uniform(tensor):
        fan_in = nn.init._calculate_correct_fan(tensor, "fan_in")
        nn.init.uniform_(tensor, -math.sqrt(3 / fan_in), math.sqrt(3 / fan_in))

    for i in range(rnn.num_layers):
        concat_init(getattr(rnn, f"weight_ih_l{i}"), [inner_uniform] * 3)
        nn.init.constant_(getattr(rnn, f"bias_ih_l{i}"), 0)
        concat_init(getattr(rnn, f"weight_hh_l{i}"), [inner_uniform, inner_uniform, nn.init.orthogonal_])
        nn.init.constant_(getattr(rnn, f"bias_hh_l{i}"), 0)


class ConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels, momentum):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1), bias=False)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1), bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels, momentum)
        self.bn2 = nn.BatchNorm2d(out_channels, momentum)
        init_layer(self.conv1)
        init_layer(self.conv2)
        init_bn(self.bn1)
        init_bn(self.bn2)

    def forward(self, x, pool_size=(2, 2)):
        x = F.relu_(self.bn1(self.conv1(x)))
        x = F.relu_(self.bn2(self.conv2(x)))
        return F.avg_pool2d(x, kernel_size=pool_size)


class AcousticModelCRnn8Dropout(nn.Module):
    def __init__(self, classes_num, midfeat, momentum):
        super().__init__()
        self.conv_block1 = ConvBlock(1, 48, momentum)
        self.conv_block2 = ConvBlock(48, 64, momentum)
        self.conv_block3 = ConvBlock(64, 96, momentum)
        self.conv_block4 = ConvBlock(96, 128, momentum)
        self.fc5 = nn.Linear(midfeat, 768, bias=False)
        self.bn5 = nn.BatchNorm1d(768, momentum=momentum)
        self.gru = nn.GRU(input_size=768, hidden_size=256, num_layers=2, bias=True,
                          batch_first=True, dropout=0., bidirectional=True)
        self.fc = nn.Linear(512, classes_num, bias=True)
        init_layer(self.fc5)
        init_bn(self.bn5)
        init_gru(self.gru)
        init_layer(self.fc)

    def forward(self, x):
        for block in (self.conv_block1, self.conv_block2, self.conv_block3, self.conv_block4):
            x = block(x, pool_size=(1, 2))  # dropout is a no-op at inference
        x = x.transpose(1, 2).flatten(2)
        x = F.relu(self.bn5(self.fc5(x).transpose(1, 2)).transpose(1, 2))
        x, _ = self.gru(x)
        return torch.sigmoid(self.fc(x))


class Regress_onset_offset_frame_velocity_CRNN(nn.Module):
    """Kong et al. 2020: onset, offset, frame and velocity heads on a log-mel input."""

    def __init__(self, frames_per_second=FRAMES_PER_SECOND, classes_num=CLASSES):
        super().__init__()
        from torchlibrosa.stft import LogmelFilterBank, Spectrogram
        window_size, hop_size, mel_bins, midfeat, momentum = 2048, SAMPLE_RATE // frames_per_second, 229, 1792, 0.01
        self.spectrogram_extractor = Spectrogram(n_fft=window_size, hop_length=hop_size, win_length=window_size,
                                                 window="hann", center=True, pad_mode="reflect", freeze_parameters=True)
        self.logmel_extractor = LogmelFilterBank(sr=SAMPLE_RATE, n_fft=window_size, n_mels=mel_bins, fmin=30,
                                                 fmax=SAMPLE_RATE // 2, ref=1.0, amin=1e-10, top_db=None,
                                                 freeze_parameters=True)
        self.bn0 = nn.BatchNorm2d(mel_bins, momentum)
        self.frame_model = AcousticModelCRnn8Dropout(classes_num, midfeat, momentum)
        self.reg_onset_model = AcousticModelCRnn8Dropout(classes_num, midfeat, momentum)
        self.reg_offset_model = AcousticModelCRnn8Dropout(classes_num, midfeat, momentum)
        self.velocity_model = AcousticModelCRnn8Dropout(classes_num, midfeat, momentum)
        self.reg_onset_gru = nn.GRU(input_size=88 * 2, hidden_size=256, num_layers=1, bias=True,
                                    batch_first=True, dropout=0., bidirectional=True)
        self.reg_onset_fc = nn.Linear(512, classes_num, bias=True)
        self.frame_gru = nn.GRU(input_size=88 * 3, hidden_size=256, num_layers=1, bias=True,
                                batch_first=True, dropout=0., bidirectional=True)
        self.frame_fc = nn.Linear(512, classes_num, bias=True)
        init_bn(self.bn0)
        init_gru(self.reg_onset_gru)
        init_gru(self.frame_gru)
        init_layer(self.reg_onset_fc)
        init_layer(self.frame_fc)

    def forward(self, audio):
        x = self.logmel_extractor(self.spectrogram_extractor(audio))
        x = self.bn0(x.transpose(1, 3)).transpose(1, 3)
        frame = self.frame_model(x)
        onset = self.reg_onset_model(x)
        offset = self.reg_offset_model(x)
        velocity = self.velocity_model(x)
        y, _ = self.reg_onset_gru(torch.cat((onset, (onset ** 0.5) * velocity.detach()), dim=2))
        onset = torch.sigmoid(self.reg_onset_fc(y))
        y, _ = self.frame_gru(torch.cat((frame, onset.detach(), offset.detach()), dim=2))
        frame = torch.sigmoid(self.frame_fc(y))
        return {"reg_onset_output": onset, "reg_offset_output": offset,
                "frame_output": frame, "velocity_output": velocity}


# ---------------------------------------------------------------- running it

def run_model(model: nn.Module, audio: np.ndarray, batch_size: int = 8) -> dict[str, np.ndarray]:
    """16 kHz mono audio in; per-frame outputs (frames, 88) out.

    10 s segments overlapping by half; each keeps its middle half when they are
    joined (PianoTranscription.transcribe/enframe/deframe).
    """
    n = len(audio)
    pad = int(np.ceil(n / SEGMENT_SAMPLES)) * SEGMENT_SAMPLES - n
    x = np.concatenate((audio, np.zeros(pad)))[None, :]
    segs = np.concatenate([x[:, p:p + SEGMENT_SAMPLES]
                           for p in range(0, x.shape[1] - SEGMENT_SAMPLES + 1, SEGMENT_SAMPLES // 2)], axis=0)
    device = next(model.parameters()).device
    out: dict[str, list] = {}
    model.eval()
    for p in range(0, len(segs), batch_size):
        with torch.no_grad():
            batch = model(torch.as_tensor(segs[p:p + batch_size], dtype=torch.float32, device=device))
        for k, v in batch.items():
            out.setdefault(k, []).append(v.cpu().numpy())
    return {k: deframe(np.concatenate(v, axis=0))[:n] for k, v in out.items()}


def deframe(x: np.ndarray) -> np.ndarray:
    if x.shape[0] == 1:
        return x[0]
    x = x[:, :-1, :]  # one extra frame per segment from the centred STFT
    _, frames, _ = x.shape
    parts = [x[0, :int(frames * 0.75)]]
    parts += [x[i, int(frames * 0.25):int(frames * 0.75)] for i in range(1, x.shape[0] - 1)]
    parts.append(x[-1, int(frames * 0.25):])
    return np.concatenate(parts, axis=0)


# ---------------------------------------------------------------- decoding notes

def decode(output: dict[str, np.ndarray], onset_threshold: float, offset_threshold: float,
           frame_threshold: float) -> list[dict]:
    """Frame outputs to notes [{onset, offset, pitch, velocity}] (RegressionPostProcessor)."""
    onset, onset_shift = binarize(output["reg_onset_output"], onset_threshold, 2)
    offset, offset_shift = binarize(output["reg_offset_output"], offset_threshold, 4)
    notes = []
    for k in range(output["frame_output"].shape[-1]):
        for bgn, fin, on_shift, off_shift, vel in detect(output["frame_output"][:, k], onset[:, k], onset_shift[:, k],
                                                         offset[:, k], offset_shift[:, k],
                                                         output["velocity_output"][:, k], frame_threshold):
            notes.append({"onset": float(np.float32((bgn + on_shift) / FRAMES_PER_SECOND)),
                          "offset": float(np.float32((fin + off_shift) / FRAMES_PER_SECOND)),
                          "pitch": k + BEGIN_NOTE, "velocity": int(np.float32(vel) * VELOCITY_SCALE)})
    return notes


def binarize(reg: np.ndarray, threshold: float, neighbour: int) -> tuple[np.ndarray, np.ndarray]:
    """A peak over threshold that rises for `neighbour` frames and falls after,
    with its sub-frame position (Kong et al. 2020, section III-D)."""
    binary, shift = np.zeros_like(reg), np.zeros_like(reg)
    frames, classes = reg.shape
    for k in range(classes):
        x = reg[:, k]
        for n in np.flatnonzero(x[neighbour:frames - neighbour] > threshold) + neighbour:
            if not all(x[n - i] >= x[n - i - 1] and x[n + i] >= x[n + i + 1] for i in range(neighbour)):
                continue
            binary[n, k] = 1
            if x[n - 1] > x[n + 1]:
                shift[n, k] = (x[n + 1] - x[n - 1]) / (x[n] - x[n + 1]) / 2 if x[n] != x[n + 1] else 0.0
            else:
                shift[n, k] = (x[n + 1] - x[n - 1]) / (x[n] - x[n - 1]) / 2 if x[n] != x[n - 1] else 0.0
    return binary, shift


def detect(frame, onset, onset_shift, offset, offset_shift, velocity, frame_threshold) -> list[list]:
    """One pitch's notes: start at each onset, end where the frame output drops
    or an offset is found, whichever fits (piano_vad.note_detection_with_onset_offset_regress)."""
    out = []
    bgn = frame_disappear = offset_occur = None
    for i in range(onset.shape[0]):
        if onset[i] == 1:
            if bgn:  # a new onset ends the ringing note
                out.append([bgn, max(i - 1, 0), onset_shift[bgn], 0, velocity[bgn]])
                frame_disappear, offset_occur = None, None
            bgn = i
        if bgn and i > bgn:
            if frame[i] <= frame_threshold and not frame_disappear:
                frame_disappear = i
            if offset[i] == 1 and not offset_occur:
                offset_occur = i
            if frame_disappear:
                fin = offset_occur if offset_occur and offset_occur - bgn > frame_disappear - offset_occur else frame_disappear
                out.append([bgn, fin, onset_shift[bgn], offset_shift[fin], velocity[bgn]])
                bgn, frame_disappear, offset_occur = None, None, None
            if bgn and (i - bgn >= 600 or i == onset.shape[0] - 1):
                out.append([bgn, i, onset_shift[bgn], offset_shift[i], velocity[bgn]])
                bgn, frame_disappear, offset_occur = None, None, None
    out.sort(key=lambda t: t[0])
    return out
