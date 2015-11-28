#
# public function used by CUIT web site
#
def try_times(try_time):
    def decorator(f):
        def wrapper(*args, **kwarg):
            cal_state = False
            time = try_time
            ret = None
            while time > 0 and cal_state == False:
                print 'try time', time
                try:
                    ret = f(*args, **kwarg)
                    cal_state = True
                except Exception, e:
                    cal_state = False
                finally:
                    time -=1
            if cal_state == False:
                raise Exception('func'+ f.__name__ + 'call failed')
            return ret
        return wrapper
    return decorator