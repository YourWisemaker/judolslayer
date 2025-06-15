import { useMutation } from '@tanstack/react-query';
import { spamDetectionAPI, SpamDetectionRequest, SpamDetectionResponse } from '@/lib/api';
import toast from 'react-hot-toast';

export const useSpamDetection = () => {
  return useMutation<SpamDetectionResponse, Error, SpamDetectionRequest>({
    mutationFn: spamDetectionAPI.processVideo,
    onError: (error) => {
      console.error('Spam detection error:', error);
      toast.error(error.message || 'Failed to process video');
    },
    onSuccess: (data) => {
      if (!data.success) {
        toast.error('Processing failed');
      }
    },
  });
};