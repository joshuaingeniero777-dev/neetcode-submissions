class Solution:
    def hasDuplicate(self, nums: List[int]) -> bool:
        
        my_set = set(nums);
        set_length = len(my_set);
        if len(my_set) != len(nums): 
            return  True;
        else:
            return False;