import re
import json
import argparse
import numpy as np
import spacy


def build_vocab(vids, params):
    # 默认为 1
    count_thr = params['word_count_threshold']
    # count up the number of words
    counts = {}
    for vid, caps in vids.items():
        for cap in caps['captions']:
            ws = re.sub(r'[.!,;?]', ' ', cap).split()
            for w in ws:
                counts[w] = counts.get(w, 0) + 1
    # cw = sorted([(count, w) for w, count in counts.items()], reverse=True)
    total_words = sum(counts.values())
    bad_words = [w for w, n in counts.items() if n <= count_thr]
    vocab = [w for w, n in counts.items() if n > count_thr]
    bad_count = sum(counts[w] for w in bad_words)
    print('number of bad words: %d/%d = %.2f%%' %
          (len(bad_words), len(counts), len(bad_words) * 100.0 / len(counts)))
    print('number of words in vocab would be %d' % len(vocab))
    print('number of UNKs: %d/%d = %.2f%%' %
          (bad_count, total_words, bad_count * 100.0 / total_words))
    # lets now produce the final annotations
    if bad_count > 0:
        # additional special UNK token we will use below to map infrequent words to
        print('inserting the special UNK token')
        vocab.append('<UNK>')
    for vid, caps in vids.items():
        caps = caps['captions']
        vids[vid]['final_captions'] = []
        for cap in caps:
            ws = re.sub(r'[.!,;?]', ' ', cap).split()
            caption = ['<sos>'] + [w if counts.get(w, 0) > count_thr else '<UNK>' for w in ws] + ['<eos>']
            vids[vid]['final_captions'].append(caption)
    spc = spacy.load('en_core_web_sm')
    # 默认为 summary_data/info.json
    with open(params['vid_json'], 'r') as f:
        vid = json.load(f)
        for i in vid['videos'].keys():
            text = vid['videos'][i]['caption']
            words = [tok.text.lower() for tok in spc.tokenizer(text)]
            for w in words:
                if w not in vocab:
                    print("Add word %s from summe and tvsum." % w)
                    vocab.append(w.lower())
    return vocab


def main(params):
    # 默认为 dataset/msvd/all_info.json
    videos = json.load(open(params['msrv_json'], 'r'))['sentences']
    video_caption = {}
    for video in videos:
        video_id = video['video_id']
        if video_id not in video_caption.keys():
            video_caption[video_id] = {'captions': []}
        video_caption[video_id]['captions'].append(video['caption'])

    print(f"video_caption: {video_caption}")
    # create the vocab
    vocab = build_vocab(video_caption, params)
    itow = {i + 2: w for i, w in enumerate(vocab)}
    wtoi = {w: i + 2 for i, w in enumerate(vocab)}  # inverse table
    wtoi['<eos>'] = 0
    itow[0] = '<eos>'
    wtoi['<sos>'] = 1
    itow[1] = '<sos>'
    out = {}
    out['ix_to_word'] = itow
    out['word_to_ix'] = wtoi
    out['videos'] = {'train': [], 'validate': [], 'test': []}
    # 默认为 dataset/msvd/all_info.json
    videos = json.load(open(params['msrv_json'], 'r'))['videos']
    for video in videos:
        out['videos'][video['split']].append(int(video['id']))

    # 默认为 out_path/info.json
    with open(params['info_json'], 'w') as f:
        json.dump(out, f, indent=4)
    # 默认为 out_path/caption.json
    with open(params['caption_json'], 'w') as f:
        json.dump(video_caption, f, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # input json
    parser.add_argument('--msrv_json', type=str, default='/Users/bytedance/Downloads/train_val_test_annotation/train_val_videodatainfo.json',
                        help='msr_vtt videoinfo json')
    parser.add_argument('--vid_json', type=str, default='summary_data/info.json',
                        help='tvsum and summe videoinfo json')
    parser.add_argument('--info_json', default='out_path/info.json',
                        help='info about iw2word and word2ix')
    parser.add_argument('--caption_json', default='out_path/caption.json', help='caption json file')

    parser.add_argument('--word_count_threshold', default=1, type=int,
                        help='only words that occur more than this number of times will be put in vocab')

    args = parser.parse_args()
    params = vars(args)  # convert to ordinary dict
    main(params)
